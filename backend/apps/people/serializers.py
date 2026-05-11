"""
Serializers do app people (Bloco 1.2).

Padrao adotado: 3 serializers por modelo (List/Detail/Write).
- List   — campos enxutos para listagem.
- Detail — completo, para `retrieve`.
- Write  — para `create`/`update`, com validacao e normalizacao.

Validators de dominio brasileiro vivem em `apps.core.validators` e sao
chamados a partir dos `validate_<campo>` deste arquivo (HTTP boundary).
"""

from __future__ import annotations

from datetime import date

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from apps.core.validators import validar_cpf, validar_pis_pasep
from apps.people.models import (
    Cargo,
    Dependente,
    Documento,
    Lotacao,
    Servidor,
    VinculoFuncional,
)

# ============================================================
# Cargo
# ============================================================


class CargoListSerializer(serializers.ModelSerializer):
    """Versao enxuta para listagem."""

    nivel_escolaridade_display = serializers.CharField(
        source="get_nivel_escolaridade_display", read_only=True
    )

    class Meta:
        model = Cargo
        fields = [
            "id",
            "codigo",
            "nome",
            "nivel_escolaridade",
            "nivel_escolaridade_display",
            "ativo",
        ]
        read_only_fields = fields


class CargoDetailSerializer(serializers.ModelSerializer):
    """Versao completa para retrieve."""

    nivel_escolaridade_display = serializers.CharField(
        source="get_nivel_escolaridade_display", read_only=True
    )

    class Meta:
        model = Cargo
        fields = [
            "id",
            "codigo",
            "nome",
            "cbo",
            "nivel_escolaridade",
            "nivel_escolaridade_display",
            "ativo",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["id", "criado_em", "atualizado_em", "nivel_escolaridade_display"]


class CargoWriteSerializer(serializers.ModelSerializer):
    """Versao para create/update."""

    class Meta:
        model = Cargo
        fields = ["id", "codigo", "nome", "cbo", "nivel_escolaridade", "ativo"]
        read_only_fields = ["id"]

    def validate_codigo(self, value: str) -> str:
        valor = value.strip().upper()
        if not valor:
            raise serializers.ValidationError("Codigo nao pode ser vazio.")
        return valor

    def validate_cbo(self, value: str) -> str:
        # CBO e opcional no Bloco 1.2; validacao contra tabela so no Bloco 4
        return (value or "").strip()


# ============================================================
# Lotacao
# ============================================================


class LotacaoListSerializer(serializers.ModelSerializer):
    """Versao enxuta para listagem."""

    natureza_display = serializers.CharField(source="get_natureza_display", read_only=True)

    class Meta:
        model = Lotacao
        fields = ["id", "codigo", "nome", "sigla", "natureza", "natureza_display", "ativo"]
        read_only_fields = fields


class LotacaoDetailSerializer(serializers.ModelSerializer):
    """Versao completa com resumo do pai."""

    lotacao_pai_nome = serializers.CharField(
        source="lotacao_pai.nome", read_only=True, default=None
    )
    natureza_display = serializers.CharField(source="get_natureza_display", read_only=True)

    class Meta:
        model = Lotacao
        fields = [
            "id",
            "codigo",
            "nome",
            "sigla",
            "natureza",
            "natureza_display",
            "lotacao_pai",
            "lotacao_pai_nome",
            "ativo",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = [
            "id",
            "criado_em",
            "atualizado_em",
            "lotacao_pai_nome",
            "natureza_display",
        ]


class LotacaoWriteSerializer(serializers.ModelSerializer):
    """Versao para create/update."""

    class Meta:
        model = Lotacao
        fields = ["id", "codigo", "nome", "sigla", "natureza", "lotacao_pai", "ativo"]
        read_only_fields = ["id"]

    def validate_codigo(self, value: str) -> str:
        valor = value.strip().upper()
        if not valor:
            raise serializers.ValidationError("Codigo nao pode ser vazio.")
        return valor

    def validate(self, attrs: dict) -> dict:
        # Impede ciclo: lotacao_pai != self
        instance = getattr(self, "instance", None)
        pai = attrs.get("lotacao_pai")
        if instance and pai and pai.pk == instance.pk:
            raise serializers.ValidationError(
                {"lotacao_pai": "Uma lotacao nao pode ser pai de si mesma."}
            )
        return attrs


# ============================================================
# Helpers de validacao reutilizaveis
# ============================================================


def _validar_cpf(value: str) -> str:
    """Wrapper que traduz Django ValidationError para DRF."""
    if not value:
        return value
    try:
        return validar_cpf(value)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(exc.message, code=exc.code) from exc


def _validar_pis_opcional(value: str) -> str:
    if not value:
        return ""
    try:
        return validar_pis_pasep(value)
    except DjangoValidationError as exc:
        raise serializers.ValidationError(exc.message, code=exc.code) from exc


def _validar_data_nao_futura(value: date, nome_campo: str = "data") -> date:
    if value and value > date.today():
        raise serializers.ValidationError(f"{nome_campo} nao pode ser futura.", code="DATA_FUTURA")
    return value


# ============================================================
# Servidor
# ============================================================


class _DependenteEmbutidoSerializer(serializers.ModelSerializer):
    """Embutido em ServidorDetailSerializer."""

    class Meta:
        model = Dependente
        fields = ["id", "nome", "parentesco", "data_nascimento", "ir", "salario_familia"]


class _VinculoEmbutidoSerializer(serializers.ModelSerializer):
    """Embutido em ServidorDetailSerializer (apenas vinculos ativos)."""

    cargo_nome = serializers.CharField(source="cargo.nome", read_only=True)
    lotacao_nome = serializers.CharField(source="lotacao.nome", read_only=True)
    regime_display = serializers.CharField(source="get_regime_display", read_only=True)

    class Meta:
        model = VinculoFuncional
        fields = [
            "id",
            "cargo",
            "cargo_nome",
            "lotacao",
            "lotacao_nome",
            "regime",
            "regime_display",
            "data_admissao",
            "data_demissao",
            "carga_horaria",
            "salario_base",
            "ativo",
        ]


class ServidorListSerializer(serializers.ModelSerializer):
    """Versao enxuta — uso em listagem (paginada)."""

    class Meta:
        model = Servidor
        fields = ["id", "matricula", "nome", "cpf", "ativo"]
        read_only_fields = fields


class ServidorDetailSerializer(serializers.ModelSerializer):
    """Versao completa — inclui dependentes e vinculos."""

    dependentes = _DependenteEmbutidoSerializer(many=True, read_only=True)
    vinculos = _VinculoEmbutidoSerializer(many=True, read_only=True)
    sexo_display = serializers.CharField(source="get_sexo_display", read_only=True)
    estado_civil_display = serializers.CharField(
        source="get_estado_civil_display", read_only=True, default=""
    )

    class Meta:
        model = Servidor
        fields = [
            "id",
            "matricula",
            "nome",
            "cpf",
            "data_nascimento",
            "sexo",
            "sexo_display",
            "estado_civil",
            "estado_civil_display",
            "pis_pasep",
            "email",
            "telefone",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "cidade",
            "uf",
            "cep",
            "ativo",
            "criado_em",
            "atualizado_em",
            "dependentes",
            "vinculos",
        ]
        read_only_fields = [
            "id",
            "criado_em",
            "atualizado_em",
            "dependentes",
            "vinculos",
            "sexo_display",
            "estado_civil_display",
        ]


class ServidorWriteSerializer(serializers.ModelSerializer):
    """Validacao + normalizacao de CPF/PIS/datas."""

    class Meta:
        model = Servidor
        fields = [
            "id",
            "matricula",
            "nome",
            "cpf",
            "data_nascimento",
            "sexo",
            "estado_civil",
            "pis_pasep",
            "email",
            "telefone",
            "logradouro",
            "numero",
            "complemento",
            "bairro",
            "cidade",
            "uf",
            "cep",
            "ativo",
        ]
        read_only_fields = ["id"]

    def validate_matricula(self, value: str) -> str:
        valor = (value or "").strip()
        if not valor:
            raise serializers.ValidationError("Matricula nao pode ser vazia.")
        return valor

    def validate_nome(self, value: str) -> str:
        valor = (value or "").strip()
        if len(valor) < 2:
            raise serializers.ValidationError("Nome muito curto.")
        return valor

    def validate_cpf(self, value: str) -> str:
        return _validar_cpf(value)

    def validate_pis_pasep(self, value: str) -> str:
        return _validar_pis_opcional(value)

    def validate_data_nascimento(self, value: date) -> date:
        _validar_data_nao_futura(value, "Data de nascimento")
        # Idade minima 14 anos (estagiario menor de aprendiz e excecao do Bloco 4+)
        idade = (date.today() - value).days / 365.25
        if idade < 14:
            raise serializers.ValidationError(
                "Servidor deve ter ao menos 14 anos.", code="IDADE_MINIMA"
            )
        return value

    def validate_uf(self, value: str) -> str:
        return (value or "").strip().upper()


# ============================================================
# VinculoFuncional
# ============================================================


class VinculoListSerializer(serializers.ModelSerializer):
    servidor_matricula = serializers.CharField(source="servidor.matricula", read_only=True)
    servidor_nome = serializers.CharField(source="servidor.nome", read_only=True)
    cargo_nome = serializers.CharField(source="cargo.nome", read_only=True)
    lotacao_sigla = serializers.CharField(source="lotacao.sigla", read_only=True)

    class Meta:
        model = VinculoFuncional
        fields = [
            "id",
            "servidor",
            "servidor_matricula",
            "servidor_nome",
            "cargo",
            "cargo_nome",
            "lotacao",
            "lotacao_sigla",
            "regime",
            "data_admissao",
            "data_demissao",
            "ativo",
        ]
        read_only_fields = fields


class VinculoDetailSerializer(serializers.ModelSerializer):
    cargo_nome = serializers.CharField(source="cargo.nome", read_only=True)
    lotacao_nome = serializers.CharField(source="lotacao.nome", read_only=True)
    regime_display = serializers.CharField(source="get_regime_display", read_only=True)

    class Meta:
        model = VinculoFuncional
        fields = [
            "id",
            "servidor",
            "cargo",
            "cargo_nome",
            "lotacao",
            "lotacao_nome",
            "regime",
            "regime_display",
            "data_admissao",
            "data_demissao",
            "carga_horaria",
            "salario_base",
            "ativo",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = [
            "id",
            "criado_em",
            "atualizado_em",
            "cargo_nome",
            "lotacao_nome",
            "regime_display",
        ]


class VinculoWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = VinculoFuncional
        fields = [
            "id",
            "servidor",
            "cargo",
            "lotacao",
            "regime",
            "data_admissao",
            "data_demissao",
            "carga_horaria",
            "salario_base",
            "ativo",
        ]
        read_only_fields = ["id"]

    def validate_data_admissao(self, value: date) -> date:
        return _validar_data_nao_futura(value, "Data de admissao")

    def validate_carga_horaria(self, value: int) -> int:
        if value <= 0 or value > 60:
            raise serializers.ValidationError(
                "Carga horaria deve estar entre 1 e 60 horas semanais."
            )
        return value

    def validate(self, attrs: dict) -> dict:
        admissao = attrs.get("data_admissao") or getattr(self.instance, "data_admissao", None)
        demissao = attrs.get("data_demissao") or getattr(self.instance, "data_demissao", None)
        if admissao and demissao and demissao < admissao:
            raise serializers.ValidationError(
                {"data_demissao": "Data de demissao nao pode ser anterior a admissao."}
            )
        return attrs


# ============================================================
# Dependente
# ============================================================


class DependenteListSerializer(serializers.ModelSerializer):
    parentesco_display = serializers.CharField(source="get_parentesco_display", read_only=True)

    class Meta:
        model = Dependente
        fields = [
            "id",
            "servidor",
            "nome",
            "parentesco",
            "parentesco_display",
            "data_nascimento",
            "ir",
            "salario_familia",
        ]
        read_only_fields = fields


class DependenteDetailSerializer(serializers.ModelSerializer):
    parentesco_display = serializers.CharField(source="get_parentesco_display", read_only=True)

    class Meta:
        model = Dependente
        fields = [
            "id",
            "servidor",
            "nome",
            "cpf",
            "data_nascimento",
            "parentesco",
            "parentesco_display",
            "ir",
            "salario_familia",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["id", "criado_em", "atualizado_em", "parentesco_display"]


class DependenteWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dependente
        fields = [
            "id",
            "servidor",
            "nome",
            "cpf",
            "data_nascimento",
            "parentesco",
            "ir",
            "salario_familia",
        ]
        read_only_fields = ["id"]

    def validate_cpf(self, value: str) -> str:
        return _validar_cpf(value)

    def validate_data_nascimento(self, value: date) -> date:
        return _validar_data_nao_futura(value, "Data de nascimento")


# ============================================================
# Documento
# ============================================================


class DocumentoListSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = Documento
        fields = [
            "id",
            "servidor",
            "tipo",
            "tipo_display",
            "descricao",
            "arquivo",
            "data_upload",
        ]
        read_only_fields = fields


class DocumentoDetailSerializer(DocumentoListSerializer):
    """Mesmo que List por ora — todos os campos sao basicos."""


class DocumentoWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Documento
        fields = ["id", "servidor", "tipo", "descricao", "arquivo"]
        read_only_fields = ["id"]


# ============================================================
# Historico (simple_history) — Servidor
# ============================================================


class HistoricoServidorSerializer(serializers.Serializer):
    """Snapshot historico do Servidor.

    `simple_history` cria HistoricalServidor com os campos do model + 4 extras
    (history_date, history_type, history_change_reason, history_user).
    """

    history_id = serializers.IntegerField(read_only=True)
    history_date = serializers.DateTimeField(read_only=True)
    history_type = serializers.CharField(read_only=True)
    history_change_reason = serializers.CharField(read_only=True, allow_null=True)
    history_user_email = serializers.SerializerMethodField()

    matricula = serializers.CharField(read_only=True)
    nome = serializers.CharField(read_only=True)
    cpf = serializers.CharField(read_only=True)
    ativo = serializers.BooleanField(read_only=True)

    def get_history_user_email(self, obj) -> str | None:
        user = getattr(obj, "history_user", None)
        return user.email if user else None


# ============================================================
# Serializers de input para os endpoints de acao (Bloco 1.2 — Onda 3)
# ============================================================


class AdmissaoInputSerializer(serializers.Serializer):
    """Input para POST /api/people/servidores/admitir/.

    Espelha apps.people.services.admissao.DadosAdmissao.
    """

    matricula = serializers.CharField(max_length=30)
    nome = serializers.CharField(max_length=200)
    cpf = serializers.CharField(max_length=14)
    data_nascimento = serializers.DateField()
    sexo = serializers.CharField(max_length=1)
    estado_civil = serializers.CharField(max_length=20, required=False, allow_blank=True)
    pis_pasep = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    telefone = serializers.CharField(max_length=20, required=False, allow_blank=True)

    cargo_id = serializers.IntegerField()
    lotacao_id = serializers.IntegerField()
    regime = serializers.CharField(max_length=30)
    data_admissao = serializers.DateField()
    salario_base = serializers.DecimalField(max_digits=12, decimal_places=2)
    carga_horaria = serializers.IntegerField(default=40, min_value=1, max_value=60)


class DesligamentoInputSerializer(serializers.Serializer):
    """Input para POST /api/people/servidores/<id>/desligar/."""

    data_desligamento = serializers.DateField()
    motivo = serializers.CharField(required=False, allow_blank=True, max_length=500)


class TransferenciaInputSerializer(serializers.Serializer):
    """Input para POST /api/people/vinculos/<id>/transferir/."""

    nova_lotacao_id = serializers.IntegerField()
    data_transferencia = serializers.DateField()
