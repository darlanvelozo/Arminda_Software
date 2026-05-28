"""
Modelos do app people (TENANT_APPS).

Vivem dentro do schema de cada municipio. Sem FK explicita para Municipio:
o tenant e implicito via search_path do Postgres (ADR-0006).
Auditoria de quem criou/atualizou via TimeStampedModel (apps.core).
Historico via simple-history.
"""

from __future__ import annotations

from django.db import models
from simple_history.models import HistoricalRecords

from apps.core.models import TimeStampedModel


class NivelEscolaridade(models.TextChoices):
    FUNDAMENTAL = "fundamental", "Fundamental"
    MEDIO = "medio", "Medio"
    TECNICO = "tecnico", "Tecnico"
    SUPERIOR = "superior", "Superior"
    POS_GRADUACAO = "pos_graduacao", "Pos-graduacao"


class Sexo(models.TextChoices):
    MASCULINO = "M", "Masculino"
    FEMININO = "F", "Feminino"


class EstadoCivil(models.TextChoices):
    SOLTEIRO = "solteiro", "Solteiro(a)"
    CASADO = "casado", "Casado(a)"
    DIVORCIADO = "divorciado", "Divorciado(a)"
    VIUVO = "viuvo", "Viuvo(a)"
    UNIAO_ESTAVEL = "uniao_estavel", "Uniao estavel"


class Regime(models.TextChoices):
    ESTATUTARIO = "estatutario", "Efetivo (concursado)"
    CELETISTA = "celetista", "Celetista"
    COMISSIONADO = "comissionado", "Comissionado"
    TEMPORARIO = "temporario", "Contratado temporario"
    ELETIVO = "eletivo", "Eletivo"
    ESTAGIARIO = "estagiario", "Estagiario"


class NaturezaLotacao(models.TextChoices):
    """Classificação macro da lotação por secretaria/área de atuação."""

    ADMINISTRACAO = "administracao", "Administração"
    SAUDE = "saude", "Saúde"
    EDUCACAO = "educacao", "Educação"
    ASSISTENCIA = "assistencia_social", "Assistência social"
    OUTROS = "outros", "Outros"


class Parentesco(models.TextChoices):
    CONJUGE = "conjuge", "Conjuge"
    FILHO = "filho", "Filho(a)"
    ENTEADO = "enteado", "Enteado(a)"
    PAI_MAE = "pai_mae", "Pai/Mae"
    OUTRO = "outro", "Outro"


class TipoDocumento(models.TextChoices):
    RG = "rg", "RG"
    CPF = "cpf", "CPF"
    TITULO_ELEITOR = "titulo_eleitor", "Titulo de eleitor"
    CARTEIRA_TRABALHO = "carteira_trabalho", "Carteira de trabalho"
    CERTIFICADO = "certificado", "Certificado/Diploma"
    COMPROVANTE_RESIDENCIA = "comprovante_residencia", "Comprovante de residencia"
    OUTRO = "outro", "Outro"


class TipoLogradouro(models.TextChoices):
    """Tipo de logradouro conforme tabela do eSocial S-2200 (Onda 1.6a)."""

    RUA = "rua", "Rua"
    AVENIDA = "avenida", "Avenida"
    PRACA = "praca", "Praça"
    TRAVESSA = "travessa", "Travessa"
    RODOVIA = "rodovia", "Rodovia"
    ESTRADA = "estrada", "Estrada"
    VIELA = "viela", "Viela"
    ALAMEDA = "alameda", "Alameda"
    LARGO = "largo", "Largo"
    OUTRO = "outro", "Outro"


# ============================================================
# Cargo
# ============================================================


class Cargo(TimeStampedModel):
    """Cargo publico (ex: Professor, Enfermeiro, Auxiliar Administrativo)."""

    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=200)
    cbo = models.CharField("CBO", max_length=10, blank=True)
    nivel_escolaridade = models.CharField(
        max_length=30,
        choices=NivelEscolaridade.choices,
        default=NivelEscolaridade.MEDIO,
    )
    ativo = models.BooleanField(default=True)

    # Campos enriquecidos (Bloco 1.4 — vindos do SIP/eSocial; opcionais)
    data_criacao = models.DateField(null=True, blank=True)
    data_extincao = models.DateField(null=True, blank=True)
    vagas_total = models.PositiveIntegerField(null=True, blank=True)
    dedicacao_exclusiva = models.BooleanField(default=False)
    atribuicoes = models.TextField(blank=True)

    history = HistoricalRecords(excluded_fields=["atualizado_em"])

    class Meta:
        ordering = ["nome"]
        verbose_name = "cargo"
        verbose_name_plural = "cargos"

    def __str__(self) -> str:
        return f"{self.codigo} - {self.nome}"


# ============================================================
# Lotacao
# ============================================================


class UnidadeOrcamentaria(TimeStampedModel):
    """
    Unidade orçamentária — de onde sai o empenho do vínculo (Onda 1.4-bis).

    Modela o conceito do Fiorilli SIP `DEPDESPESA × ANO`: cada município
    tem ~65 unidades por exercício fiscal, e cada vínculo aponta para uma
    delas. É a fonte de verdade da divisão por secretaria/área, mesmo
    quando a lotação física diverge (servidor fisicamente no Centro
    Administrativo, mas pago pela SEMSA).
    """

    codigo = models.CharField(
        max_length=10,
        help_text="Código no SIP (DEPDESPESA), ex.: '201013'.",
    )
    codigo_interno_sip = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text=(
            "PK interno (UNIDADE.CODIGO) do Fiorilli SIP. É por ele que "
            "TRABALHADOR.DEPDESPESA aponta — o nome do campo no SIP é enganoso."
        ),
    )
    ano = models.PositiveIntegerField(help_text="Exercício fiscal.")
    nome = models.CharField(max_length=200)
    sigla = models.CharField(max_length=20, blank=True)
    natureza = models.CharField(
        max_length=30,
        choices=NaturezaLotacao.choices,
        default=NaturezaLotacao.OUTROS,
    )
    # ADR-0011: cada unidade orçamentária pode ser empenhada por um órgão
    # emissor (CNPJ próprio). Tornado realidade na Onda 1.6a.
    orgao_emissor = models.ForeignKey(
        "people.OrgaoEmissor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="unidades_orcamentarias",
        help_text="CNPJ que assina os empenhos desta unidade orçamentária.",
    )
    ativo = models.BooleanField(default=True)

    history = HistoricalRecords(excluded_fields=["atualizado_em"])

    class Meta:
        ordering = ["-ano", "codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["codigo", "ano"], name="unidade_unica_por_codigo_e_ano"
            ),
        ]
        verbose_name = "unidade orçamentária"
        verbose_name_plural = "unidades orçamentárias"

    def __str__(self) -> str:
        return f"{self.codigo}/{self.ano} — {self.nome}"


class Lotacao(TimeStampedModel):
    """Lotacao/Secretaria (ex: Secretaria de Educacao, Saude)."""

    codigo = models.CharField(max_length=20, unique=True)
    nome = models.CharField(max_length=200)
    sigla = models.CharField(max_length=20, blank=True)
    natureza = models.CharField(
        max_length=30,
        choices=NaturezaLotacao.choices,
        default=NaturezaLotacao.OUTROS,
        help_text="Classificação macro: administração, saúde, educação, assistência social ou outros.",
    )
    lotacao_pai = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sublotacoes",
    )
    ativo = models.BooleanField(default=True)

    history = HistoricalRecords(excluded_fields=["atualizado_em"])

    class Meta:
        ordering = ["nome"]
        verbose_name = "lotacao"
        verbose_name_plural = "lotacoes"

    def __str__(self) -> str:
        return f"{self.sigla or self.codigo} - {self.nome}"


# ============================================================
# Servidor
# ============================================================


class Servidor(TimeStampedModel):
    """Servidor publico municipal."""

    matricula = models.CharField(max_length=30, unique=True)
    nome = models.CharField(max_length=200)
    cpf = models.CharField("CPF", max_length=14)
    data_nascimento = models.DateField()
    sexo = models.CharField(max_length=1, choices=Sexo.choices)
    estado_civil = models.CharField(max_length=20, choices=EstadoCivil.choices, blank=True)
    pis_pasep = models.CharField("PIS/PASEP", max_length=20, blank=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)

    # Endereco (tipo_logradouro adicionado na Onda 1.6a para o S-2200 do eSocial)
    tipo_logradouro = models.CharField(
        max_length=15, choices=TipoLogradouro.choices, blank=True
    )
    logradouro = models.CharField(max_length=200, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    uf = models.CharField(max_length=2, blank=True)
    cep = models.CharField("CEP", max_length=10, blank=True)

    # Campos enriquecidos (Bloco 1.4 — vindos do SIP/eSocial; opcionais)
    nacionalidade = models.CharField(max_length=2, blank=True)
    raca = models.CharField("raça/cor", max_length=1, blank=True)
    nome_pai = models.CharField(max_length=200, blank=True)
    nome_mae = models.CharField(max_length=200, blank=True)
    instrucao = models.CharField(
        "código de instrução (eSocial)", max_length=2, blank=True
    )

    ativo = models.BooleanField(default=True)

    history = HistoricalRecords(excluded_fields=["atualizado_em"])

    class Meta:
        ordering = ["nome"]
        verbose_name = "servidor"
        verbose_name_plural = "servidores"

    def __str__(self) -> str:
        return f"{self.matricula} - {self.nome}"


# ============================================================
# Vinculo Funcional
# ============================================================


class VinculoFuncional(TimeStampedModel):
    """Vinculo do servidor com cargo e lotacao (pode ter mais de um)."""

    servidor = models.ForeignKey(Servidor, on_delete=models.CASCADE, related_name="vinculos")
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, related_name="vinculos")
    lotacao = models.ForeignKey(Lotacao, on_delete=models.PROTECT, related_name="vinculos")
    unidade_orcamentaria = models.ForeignKey(
        UnidadeOrcamentaria,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="vinculos",
        help_text="De qual orçamento sai o empenho deste vínculo (Onda 1.4-bis).",
    )
    # Campos pré-eSocial S-2200 (Onda 1.6a) — opcionais
    orgao_emissor = models.ForeignKey(
        "people.OrgaoEmissor",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="vinculos",
        help_text=(
            "Estabelecimento (CNPJ) ao qual o vínculo é atribuído no eSocial. "
            "Tipicamente Prefeitura, Câmara, Fundo de Saúde, FMAS, etc."
        ),
    )
    sindicato = models.ForeignKey(
        "people.Sindicato",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vinculos",
        help_text="Sindicato representante da categoria (S-2200 — vinculo/categoria/sindical).",
    )
    regime = models.CharField(max_length=30, choices=Regime.choices)
    data_admissao = models.DateField()
    data_demissao = models.DateField(null=True, blank=True)
    carga_horaria = models.PositiveIntegerField(help_text="Horas semanais", default=40)
    salario_base = models.DecimalField(max_digits=12, decimal_places=2)
    ativo = models.BooleanField(default=True)

    # Campos enriquecidos (Bloco 1.4 — vindos do SIP; opcionais)
    matricula_contrato = models.CharField(
        max_length=20,
        blank=True,
        help_text="Identificador do contrato no sistema legado (TRABALHADOR.REGISTRO).",
    )
    tipo_admissao = models.CharField(max_length=2, blank=True)
    processo_admissao = models.CharField(max_length=20, blank=True)

    history = HistoricalRecords(excluded_fields=["atualizado_em"])

    class Meta:
        ordering = ["-data_admissao"]
        verbose_name = "vinculo funcional"
        verbose_name_plural = "vinculos funcionais"

    def __str__(self) -> str:
        return f"{self.servidor.nome} - {self.cargo.nome} ({self.regime})"


# ============================================================
# Dependente
# ============================================================


class Dependente(TimeStampedModel):
    """Dependente de um servidor (para IR, salario-familia, etc.)."""

    servidor = models.ForeignKey(Servidor, on_delete=models.CASCADE, related_name="dependentes")
    nome = models.CharField(max_length=200)
    cpf = models.CharField("CPF", max_length=14, blank=True)
    data_nascimento = models.DateField()
    parentesco = models.CharField(max_length=30, choices=Parentesco.choices)
    ir = models.BooleanField("Dependente para IR", default=False)
    salario_familia = models.BooleanField("Salario-familia", default=False)

    class Meta:
        ordering = ["nome"]
        verbose_name = "dependente"
        verbose_name_plural = "dependentes"

    def __str__(self) -> str:
        return f"{self.nome} ({self.get_parentesco_display()})"


# ============================================================
# Documento
# ============================================================


class Documento(TimeStampedModel):
    """Documento digitalizado de um servidor."""

    servidor = models.ForeignKey(Servidor, on_delete=models.CASCADE, related_name="documentos")
    tipo = models.CharField(max_length=30, choices=TipoDocumento.choices)
    descricao = models.CharField(max_length=200, blank=True)
    arquivo = models.FileField(upload_to="documentos/%Y/%m/")
    data_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data_upload"]
        verbose_name = "documento"
        verbose_name_plural = "documentos"

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} - {self.servidor.nome}"


# ============================================================
# OrgaoEmissor — entidade fiscal autônoma com CNPJ próprio (Onda 1.6a)
# ============================================================


class OrgaoEmissor(TimeStampedModel):
    """
    Entidade fiscal com CNPJ próprio que emite obrigações (eSocial S-1005,
    MANAD, SEFIP) dentro do município. Antecipado da ADR-0011 (Bloco 4)
    para servir de FK em VinculoFuncional desde a Onda 1.6a.

    Tipicamente um município tem 3-5: Prefeitura matriz, Câmara, Fundo
    Municipal de Saúde, FMAS, IPM (regime próprio). Cada um com CNPJ
    distinto e endereço próprio que vai no envio do S-1005.
    """

    nome = models.CharField(max_length=200)
    sigla = models.CharField(max_length=20, blank=True)
    cnpj = models.CharField("CNPJ", max_length=18, unique=True)
    eh_principal = models.BooleanField(
        "É o órgão principal?",
        default=False,
        help_text="Marca a Prefeitura matriz. Apenas um por município.",
    )
    cnae_principal = models.CharField(
        "CNAE preponderante",
        max_length=7,
        blank=True,
        help_text="Código CNAE de 7 dígitos (sem separador) — usado no S-1005.",
    )
    # Endereço próprio do estabelecimento (separado do endereço do servidor)
    tipo_logradouro = models.CharField(
        max_length=15, choices=TipoLogradouro.choices, blank=True
    )
    logradouro = models.CharField(max_length=200, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    uf = models.CharField(max_length=2, blank=True)
    cep = models.CharField("CEP", max_length=10, blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    ativo = models.BooleanField(default=True)

    history = HistoricalRecords(excluded_fields=["atualizado_em"])

    class Meta:
        ordering = ["nome"]
        verbose_name = "órgão emissor"
        verbose_name_plural = "órgãos emissores"

    def __str__(self) -> str:
        return f"{self.sigla or self.nome} ({self.cnpj})"


# ============================================================
# Sindicato — pré-requisito do S-2200 do eSocial (Onda 1.6a)
# ============================================================


class Sindicato(TimeStampedModel):
    """
    Sindicato representante da categoria. Cada município pode ter vários
    sindicatos atuantes (servidores municipais, professores, agentes de
    saúde, etc.). Pré-requisito do campo `vinculo/categoria/sindical` do
    S-2200 (Admissão do trabalhador) no eSocial.
    """

    nome = models.CharField(max_length=200)
    cnpj = models.CharField("CNPJ", max_length=18, unique=True)
    codigo_sindical = models.CharField(
        "Código sindical",
        max_length=20,
        blank=True,
        help_text="Código MTE de 9 dígitos (com ou sem separador).",
    )
    categoria = models.CharField(
        "Categoria representada",
        max_length=200,
        blank=True,
        help_text="Ex.: Servidores Públicos Municipais, Trabalhadores em Educação.",
    )
    base_territorial = models.CharField(
        max_length=200,
        blank=True,
        help_text="Cidade(s) ou estado(s) onde o sindicato atua.",
    )
    ativo = models.BooleanField(default=True)

    history = HistoricalRecords(excluded_fields=["atualizado_em"])

    class Meta:
        ordering = ["nome"]
        verbose_name = "sindicato"
        verbose_name_plural = "sindicatos"

    def __str__(self) -> str:
        return self.nome
