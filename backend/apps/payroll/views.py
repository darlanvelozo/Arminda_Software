"""
ViewSets do app payroll.

- Rubrica (Bloco 1.2) — CRUD + endpoint /avaliar/ (Onda 2.1).
- Folha (Bloco 2.2) — CRUD + endpoint /calcular/.
- Lancamento (Bloco 2.2) — leitura paginada (consulta).

RBAC: leitura para qualquer papel, escrita exige financeiro/admin/staff.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.calculo.dependencias import (
    DependenciaCiclicaError,
    DependenciaInexistenteError,
)
from apps.calculo.formula.avaliador import avaliar
from apps.calculo.formula.contexto import ContextoFolha
from apps.calculo.formula.errors import FormulaError
from apps.core.permissions import IsFinanceiroMunicipio, IsLeituraMunicipio
from apps.payroll.filters import FolhaFilter, LancamentoFilter, RubricaFilter
from apps.payroll.models import Folha, Lancamento, Rubrica
from apps.payroll.serializers import (
    FolhaDetailSerializer,
    FolhaListSerializer,
    FolhaWriteSerializer,
    LancamentoSerializer,
    RubricaDetailSerializer,
    RubricaListSerializer,
    RubricaWriteSerializer,
)
from apps.payroll.services.calculo import calcular_folha


def _to_decimal_safe(v: Any) -> Any:
    """Converte um valor de entrada para Decimal quando possível.

    Inputs vindos do JSON são int/float/str — convertemos tudo para Decimal
    para preservar precisão na fórmula. Strings inválidas viram erro.
    """
    if isinstance(v, bool):
        return Decimal(int(v))
    if isinstance(v, int):
        return Decimal(v)
    if isinstance(v, float):
        return Decimal(str(v))
    if isinstance(v, str):
        try:
            return Decimal(v)
        except InvalidOperation:
            # Mantém string — pode ser argumento legítimo para função
            return v
    return v


class RubricaViewSet(viewsets.ModelViewSet):
    """CRUD de rubricas + endpoint `/avaliar/` para testar fórmula DSL.

    Engine de cálculo (apps.calculo) implementa a DSL via subset seguro
    de Python validado por AST whitelist — ver ADR-0012.
    """

    queryset = Rubrica.objects.all()
    filterset_class = RubricaFilter
    search_fields = ["codigo", "nome"]
    ordering_fields = ["codigo", "nome", "criado_em"]

    READ_ACTIONS = {"list", "retrieve", "avaliar"}

    def get_permissions(self):
        if self.action in self.READ_ACTIONS:
            return [IsLeituraMunicipio()]
        return [IsFinanceiroMunicipio()]

    def get_serializer_class(self):
        if self.action == "list":
            return RubricaListSerializer
        if self.action in ("create", "update", "partial_update"):
            return RubricaWriteSerializer
        return RubricaDetailSerializer

    @action(detail=True, methods=["post"], url_path="avaliar")
    def avaliar(self, request, pk=None):
        """
        POST /api/payroll/rubricas/{id}/avaliar/

        Avalia a fórmula da rubrica com um contexto fornecido pelo cliente.

        Body:
            {
              "contexto": {
                "SALARIO_BASE": "1320.00",
                "IDADE": 35,
                "DEPENDENTES": 2
              },
              "rubricas_calculadas": {              # opcional
                "SAL_BASE": "1320.00"
              }
            }

        Resposta:
            { "valor": "132.00", "formula": "SALARIO_BASE * 0.10" }

        Erros (HTTP 400):
            { "detail": "...", "code": "FORMULA_VARIAVEL_AUSENTE" }
        """
        rubrica: Rubrica = self.get_object()
        if not rubrica.formula or not rubrica.formula.strip():
            raise ValidationError(
                {"detail": "Rubrica não tem fórmula definida.", "code": "FORMULA_VAZIA"}
            )

        payload = request.data or {}
        variaveis_raw = payload.get("contexto") or {}
        rubricas_raw = payload.get("rubricas_calculadas") or {}

        if not isinstance(variaveis_raw, dict):
            raise ValidationError(
                {"detail": "Campo 'contexto' deve ser um objeto.", "code": "CONTEXTO_INVALIDO"}
            )

        variaveis = {k: _to_decimal_safe(v) for k, v in variaveis_raw.items()}
        rubricas_calc = {}
        for k, v in rubricas_raw.items():
            try:
                rubricas_calc[k] = Decimal(str(v))
            except InvalidOperation as exc:
                raise ValidationError(
                    {
                        "detail": f"rubricas_calculadas['{k}'] não é numérico.",
                        "code": "RUBRICA_VALOR_INVALIDO",
                    }
                ) from exc

        ctx = ContextoFolha(variaveis=variaveis, rubricas_calculadas=rubricas_calc)

        try:
            valor = avaliar(rubrica.formula, ctx)
        except FormulaError as exc:
            return Response(
                {"detail": str(exc.args[0]) if exc.args else str(exc), "code": exc.code},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"valor": str(valor), "formula": rubrica.formula})


# ============================================================
# Folha (Bloco 2.2)
# ============================================================


class FolhaViewSet(viewsets.ModelViewSet):
    """
    CRUD de folhas + endpoint `/calcular/` que dispara o cálculo
    mensal usando o engine (apps.calculo).

    Permissões:
    - list/retrieve/lancamentos: leitura (qualquer papel).
    - create/update/destroy: financeiro/admin/staff.
    - calcular: financeiro/admin/staff (é uma operação de escrita).
    """

    queryset = Folha.objects.all().order_by("-competencia", "-id")
    filterset_class = FolhaFilter
    ordering_fields = ["competencia", "tipo", "status", "criado_em"]

    READ_ACTIONS = {"list", "retrieve", "lancamentos"}

    def get_permissions(self):
        if self.action in self.READ_ACTIONS:
            return [IsLeituraMunicipio()]
        return [IsFinanceiroMunicipio()]

    def get_serializer_class(self):
        if self.action == "list":
            return FolhaListSerializer
        if self.action in ("create", "update", "partial_update"):
            return FolhaWriteSerializer
        return FolhaDetailSerializer

    @action(detail=True, methods=["post"], url_path="calcular")
    def calcular(self, request, pk=None):
        """
        POST /api/payroll/folhas/{id}/calcular/

        Executa o cálculo mensal para a competência da folha. Idempotente:
        re-rodar atualiza valores em vez de duplicar. Lançamentos órfãos
        (rubrica que deixou de ser ativa) são removidos.

        Resposta (200):
            {
              "folha_id": 1,
              "competencia": "2026-05-01",
              "vinculos_processados": 517,
              "rubricas_processadas": 8,
              "lancamentos_criados": 4136,
              "lancamentos_atualizados": 0,
              "lancamentos_removidos": 0,
              "ordem_rubricas": ["SAL_BASE", "INSS", "IRRF", ...],
              "erros": [{"vinculo_id":..., "matricula":..., "rubrica_codigo":...,
                         "code": "FORMULA_VARIAVEL_AUSENTE", "mensagem":...}]
            }

        Erros estruturais (HTTP 400):
            {"detail": "...", "code": "DEPENDENCIA_CICLICA"}
        """
        folha: Folha = self.get_object()
        try:
            relatorio = calcular_folha(folha)
        except (DependenciaCiclicaError, DependenciaInexistenteError) as exc:
            return Response(
                {"detail": str(exc.args[0]) if exc.args else str(exc), "code": exc.code},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                "folha_id": relatorio.folha_id,
                "competencia": relatorio.competencia.isoformat(),
                "vinculos_processados": relatorio.vinculos_processados,
                "rubricas_processadas": relatorio.rubricas_processadas,
                "lancamentos_criados": relatorio.lancamentos_criados,
                "lancamentos_atualizados": relatorio.lancamentos_atualizados,
                "lancamentos_removidos": relatorio.lancamentos_removidos,
                "ordem_rubricas": relatorio.ordem_rubricas,
                "erros": [
                    {
                        "vinculo_id": e.vinculo_id,
                        "matricula": e.matricula,
                        "rubrica_codigo": e.rubrica_codigo,
                        "code": e.code,
                        "mensagem": e.mensagem,
                    }
                    for e in relatorio.erros
                ],
            }
        )


# ============================================================
# Lancamento (Bloco 2.2)
# ============================================================


class LancamentoViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Consulta de lançamentos de folha. Leitura apenas — lançamentos são
    produzidos pelo cálculo da folha, nunca criados manualmente.

    Para gerar um lançamento "eventual" (fora do cálculo), use uma
    rubrica com fórmula que receba o valor via contexto — o próprio
    cálculo da folha vai produzir o lançamento.
    """

    queryset = Lancamento.objects.select_related(
        "folha", "servidor", "vinculo", "rubrica"
    ).all()
    serializer_class = LancamentoSerializer
    filterset_class = LancamentoFilter
    permission_classes = [IsLeituraMunicipio]
    ordering_fields = ["servidor__nome", "rubrica__codigo", "valor"]
    ordering = ["servidor__nome", "rubrica__codigo"]
