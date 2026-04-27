"""
Modelos do app people.

Servidores, cargos, lotacoes, vinculos funcionais e dependentes.
"""

from django.db import models

from apps.core.models import Municipio, TimeStampedModel


class Cargo(TimeStampedModel):
    """Cargo publico (ex: Professor, Enfermeiro, Auxiliar Administrativo)."""

    municipio = models.ForeignKey(
        Municipio, on_delete=models.CASCADE, related_name="cargos"
    )
    codigo = models.CharField(max_length=20)
    nome = models.CharField(max_length=200)
    cbo = models.CharField("CBO", max_length=10, blank=True)
    nivel_escolaridade = models.CharField(
        max_length=30,
        choices=[
            ("fundamental", "Fundamental"),
            ("medio", "Medio"),
            ("tecnico", "Tecnico"),
            ("superior", "Superior"),
            ("pos_graduacao", "Pos-graduacao"),
        ],
        default="medio",
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        unique_together = [("municipio", "codigo")]
        verbose_name = "cargo"
        verbose_name_plural = "cargos"

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class Lotacao(TimeStampedModel):
    """Lotacao/Secretaria (ex: Secretaria de Educacao, Saude)."""

    municipio = models.ForeignKey(
        Municipio, on_delete=models.CASCADE, related_name="lotacoes"
    )
    codigo = models.CharField(max_length=20)
    nome = models.CharField(max_length=200)
    sigla = models.CharField(max_length=20, blank=True)
    lotacao_pai = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="sublotacoes",
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        unique_together = [("municipio", "codigo")]
        verbose_name = "lotacao"
        verbose_name_plural = "lotacoes"

    def __str__(self):
        return f"{self.sigla or self.codigo} - {self.nome}"


class Servidor(TimeStampedModel):
    """Servidor publico municipal."""

    municipio = models.ForeignKey(
        Municipio, on_delete=models.CASCADE, related_name="servidores"
    )
    matricula = models.CharField(max_length=30)
    nome = models.CharField(max_length=200)
    cpf = models.CharField("CPF", max_length=14)
    data_nascimento = models.DateField()
    sexo = models.CharField(
        max_length=1,
        choices=[("M", "Masculino"), ("F", "Feminino")],
    )
    estado_civil = models.CharField(
        max_length=20,
        choices=[
            ("solteiro", "Solteiro(a)"),
            ("casado", "Casado(a)"),
            ("divorciado", "Divorciado(a)"),
            ("viuvo", "Viuvo(a)"),
            ("uniao_estavel", "Uniao estavel"),
        ],
        blank=True,
    )
    pis_pasep = models.CharField("PIS/PASEP", max_length=20, blank=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)

    # Endereco
    logradouro = models.CharField(max_length=200, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    complemento = models.CharField(max_length=100, blank=True)
    bairro = models.CharField(max_length=100, blank=True)
    cidade = models.CharField(max_length=100, blank=True)
    uf = models.CharField(max_length=2, blank=True)
    cep = models.CharField("CEP", max_length=10, blank=True)

    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]
        unique_together = [("municipio", "matricula")]
        verbose_name = "servidor"
        verbose_name_plural = "servidores"

    def __str__(self):
        return f"{self.matricula} - {self.nome}"


class VinculoFuncional(TimeStampedModel):
    """Vinculo do servidor com cargo e lotacao (pode ter mais de um)."""

    servidor = models.ForeignKey(
        Servidor, on_delete=models.CASCADE, related_name="vinculos"
    )
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, related_name="vinculos")
    lotacao = models.ForeignKey(
        Lotacao, on_delete=models.PROTECT, related_name="vinculos"
    )
    regime = models.CharField(
        max_length=30,
        choices=[
            ("estatutario", "Estatutario"),
            ("celetista", "Celetista"),
            ("comissionado", "Comissionado"),
            ("temporario", "Temporario"),
            ("estagiario", "Estagiario"),
        ],
    )
    data_admissao = models.DateField()
    data_demissao = models.DateField(null=True, blank=True)
    carga_horaria = models.PositiveIntegerField(
        help_text="Horas semanais", default=40
    )
    salario_base = models.DecimalField(max_digits=12, decimal_places=2)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["-data_admissao"]
        verbose_name = "vinculo funcional"
        verbose_name_plural = "vinculos funcionais"

    def __str__(self):
        return f"{self.servidor.nome} - {self.cargo.nome} ({self.regime})"


class Dependente(TimeStampedModel):
    """Dependente de um servidor (para IR, salario-familia, etc.)."""

    servidor = models.ForeignKey(
        Servidor, on_delete=models.CASCADE, related_name="dependentes"
    )
    nome = models.CharField(max_length=200)
    cpf = models.CharField("CPF", max_length=14, blank=True)
    data_nascimento = models.DateField()
    parentesco = models.CharField(
        max_length=30,
        choices=[
            ("conjuge", "Conjuge"),
            ("filho", "Filho(a)"),
            ("enteado", "Enteado(a)"),
            ("pai_mae", "Pai/Mae"),
            ("outro", "Outro"),
        ],
    )
    ir = models.BooleanField("Dependente para IR", default=False)
    salario_familia = models.BooleanField("Salario-familia", default=False)

    class Meta:
        ordering = ["nome"]
        verbose_name = "dependente"
        verbose_name_plural = "dependentes"

    def __str__(self):
        return f"{self.nome} ({self.get_parentesco_display()})"


class Documento(TimeStampedModel):
    """Documento digitalizado de um servidor."""

    servidor = models.ForeignKey(
        Servidor, on_delete=models.CASCADE, related_name="documentos"
    )
    tipo = models.CharField(
        max_length=30,
        choices=[
            ("rg", "RG"),
            ("cpf", "CPF"),
            ("titulo_eleitor", "Titulo de eleitor"),
            ("carteira_trabalho", "Carteira de trabalho"),
            ("certificado", "Certificado/Diploma"),
            ("comprovante_residencia", "Comprovante de residencia"),
            ("outro", "Outro"),
        ],
    )
    descricao = models.CharField(max_length=200, blank=True)
    arquivo = models.FileField(upload_to="documentos/%Y/%m/")
    data_upload = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data_upload"]
        verbose_name = "documento"
        verbose_name_plural = "documentos"

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.servidor.nome}"
