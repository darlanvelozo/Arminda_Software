"""
ViewSets do app payroll (Bloco 1.2 — Onda 3).

Apenas Rubrica esqueleto. Folha e Lancamento entram nos Blocos 2-3.
RBAC: leitura para qualquer papel, escrita exige financeiro/admin/staff.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from apps.calculo.formula.avaliador import avaliar
from apps.calculo.formula.contexto import ContextoFolha
from apps.calculo.formula.errors import FormulaError
from apps.core.permissions import IsFinanceiroMunicipio, IsLeituraMunicipio
from apps.payroll.filters import RubricaFilter
from apps.payroll.models import Rubrica
from apps.payroll.serializers import (
    RubricaDetailSerializer,
    RubricaListSerializer,
    RubricaWriteSerializer,
)


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
