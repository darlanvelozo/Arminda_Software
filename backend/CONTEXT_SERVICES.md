# backend/CONTEXT_SERVICES.md — Regras da camada de Services

> Regras para a camada de regras de negócio (`apps/<app>/services/`).
> **Antes de criar/alterar um service, ler este arquivo + [`backend/CONTEXT.md`](CONTEXT.md).**

---

## 1. O que é um service

> Service = função (ou classe) que **executa uma operação de negócio**, orquestrando models, validações, side-effects e transações.

Um service é a camada onde **a regra do produto vive**. Models guardam dados, views fazem I/O HTTP. Services fazem **trabalho**.

### Exemplos de operação que vira service
- `admitir_servidor(...)` — cria `Servidor` + `VinculoFuncional` + dispara evento eSocial S-2200 + log de auditoria.
- `calcular_folha(...)` — itera vínculos, aplica rubricas, computa incidências, persiste `Lancamento`s, atualiza totais da `Folha`.
- `importar_base_fiorilli(...)` — lê Firebird, mapeia tabelas, valida, carrega no Postgres num tenant.
- `gerar_holerite_pdf(...)` — monta PDF a partir de `Lancamento`s.

### O que NÃO é service
- ❌ `serializer.save()` chamando `Model.objects.create()`. Isso é orquestração de view, não regra. **Mas** se a criação tem regra (ex: validação cross-objeto, side-effect, evento) → tem que passar por service.
- ❌ Cálculo trivial derivado de campo próprio do model (ex: `idade()`) — fica no model.
- ❌ Filtro reutilizável de queryset — vai pra **QuerySet customizado** do model, não service.

---

## 2. Estrutura de pasta

A camada de services existe **a partir do primeiro app que precisar**. Padrão:

```
apps/people/
├── __init__.py
├── apps.py
├── models.py
├── admin.py
├── urls.py
├── views.py                       ← orquestração HTTP
├── serializers.py                 ← (a criar) DRF serializers
├── services/
│   ├── __init__.py
│   ├── exceptions.py              ← exceções de domínio do app
│   ├── admissao.py                ← admitir_servidor()
│   ├── desligamento.py            ← desligar_servidor()
│   ├── importacao_fiorilli.py     ← importar_base_fiorilli()
│   └── ...
├── tasks.py                       ← (Bloco 2+) tasks Celery
├── migrations/
└── tests/
    ├── test_models.py
    ├── test_services_admissao.py  ← um arquivo de teste por service
    └── test_views.py
```

**Regra:** um service por arquivo (ou um conjunto coeso pequeno). Arquivo grande de service = sinal de que precisa quebrar.

---

## 3. Forma do service: função primeiro

**Default:** **função pura** (no sentido prático: assinatura clara, retorno determinístico, transação explícita). Classes só quando há estado/configuração que justifique.

```python
# apps/people/services/admissao.py
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.db import transaction

from apps.core.models import Municipio
from apps.people.models import Cargo, Lotacao, Servidor, VinculoFuncional
from apps.people.services.exceptions import AdmissaoInvalidaError


@dataclass(frozen=True)
class DadosAdmissao:
    """Dados necessários para admitir um servidor.

    Use um dataclass (não dict) — força tipagem e nomeação explícita.
    """
    nome: str
    cpf: str
    data_nascimento: date
    matricula: str
    cargo_id: int
    lotacao_id: int
    regime: str
    data_admissao: date
    salario_base: Decimal
    carga_horaria: int = 40


@transaction.atomic
def admitir_servidor(municipio: Municipio, dados: DadosAdmissao) -> Servidor:
    """Admite um servidor no município.

    Cria o Servidor e seu VinculoFuncional inicial em uma única transação.

    Levanta AdmissaoInvalidaError se:
    - matrícula já existe no município
    - cargo ou lotação não pertencem ao município
    - data de admissão é futura
    """
    if Servidor.objects.filter(municipio=municipio, matricula=dados.matricula).exists():
        raise AdmissaoInvalidaError(
            f"Matrícula {dados.matricula} já existe em {municipio}",
            code="MATRICULA_DUPLICADA",
        )

    cargo = Cargo.objects.filter(id=dados.cargo_id, municipio=municipio).first()
    if not cargo:
        raise AdmissaoInvalidaError("Cargo inválido para o município", code="CARGO_INVALIDO")

    lotacao = Lotacao.objects.filter(id=dados.lotacao_id, municipio=municipio).first()
    if not lotacao:
        raise AdmissaoInvalidaError("Lotação inválida para o município", code="LOTACAO_INVALIDA")

    if dados.data_admissao > date.today():
        raise AdmissaoInvalidaError("Data de admissão não pode ser futura", code="DATA_FUTURA")

    servidor = Servidor.objects.create(
        municipio=municipio,
        matricula=dados.matricula,
        nome=dados.nome,
        cpf=dados.cpf,
        data_nascimento=dados.data_nascimento,
        sexo="",  # campo obrigatório do model — ajustar conforme dados reais
    )
    VinculoFuncional.objects.create(
        servidor=servidor,
        cargo=cargo,
        lotacao=lotacao,
        regime=dados.regime,
        data_admissao=dados.data_admissao,
        carga_horaria=dados.carga_horaria,
        salario_base=dados.salario_base,
    )
    # Side-effects (eSocial S-2200, e-mail, etc.) entram aqui no Bloco 4.
    return servidor
```

### Por que função
- **Mais fácil de testar** (sem setup de classe).
- **Mais fácil de compor** (chain de funções é trivial).
- **Sem estado escondido** (toda dependência é parâmetro).

### Quando usar classe
- Pipeline com múltiplos passos configuráveis (ex: `CalculadorFolha` com plug-ins).
- Estado interno legítimo (cache de tabelas legais durante cálculo de uma folha inteira).
- Uso intensivo de polimorfismo (estratégias diferentes por tipo de folha).

---

## 4. Transações

- **Toda escrita multi-tabela** roda dentro de `transaction.atomic()`.
- Decorator `@transaction.atomic` na função, ou bloco `with transaction.atomic():` em parte específica.
- **Não** capturar exceção dentro do bloco atômico só para "deixar passar" — deixe estourar para rollback acontecer.
- Para operações que **não** devem rollar back juntas (ex: log de erro persistido mesmo se a operação principal falhar), usar `transaction.on_commit()` para side-effects post-commit.

```python
@transaction.atomic
def desligar_servidor(servidor: Servidor, data: date, motivo: str) -> None:
    servidor.vinculos.filter(ativo=True).update(ativo=False, data_demissao=data)
    servidor.ativo = False
    servidor.save()

    # Side-effect só dispara se a transação commitar
    transaction.on_commit(lambda: _enviar_evento_esocial_s2299(servidor.id, data))
```

---

## 5. Exceções de domínio

Cada app tem suas exceções em `services/exceptions.py`:

```python
# apps/people/services/exceptions.py

class DomainError(Exception):
    """Base para erros de domínio do app people.

    Sempre carrega:
    - mensagem em português (vai para usuário final)
    - code estável (vai para logs e clientes que precisam tratar)
    """

    code: str = "ERRO_DOMINIO"

    def __init__(self, mensagem: str, *, code: str | None = None):
        super().__init__(mensagem)
        if code:
            self.code = code


class AdmissaoInvalidaError(DomainError):
    code = "ADMISSAO_INVALIDA"


class DesligamentoInvalidoError(DomainError):
    code = "DESLIGAMENTO_INVALIDO"
```

### Tradução para HTTP (em viewset)
```python
from rest_framework.exceptions import ValidationError

try:
    servidor = admitir_servidor(municipio, dados)
except DomainError as exc:
    raise ValidationError({"detail": str(exc), "code": exc.code})
```

### Não usar `Exception` genérica em código de domínio.

---

## 6. Validação no service

- Toda validação cross-objeto vive aqui (não no `Model.clean()`, que é frágil).
- Validar **cedo** — o primeiro `if not válido: raise` antes de qualquer escrita.
- Validações que **dependem de tabelas legais** (ex: tabela INSS vigente na competência) entram no service, **nunca** no model.

---

## 7. Dependências externas (e-mail, fila, HTTP)

- Service de domínio pode **disparar** side-effects, mas **a chamada externa real** (request HTTP, send_mail) deve ir para `tasks.py` (Celery) ou para um adapter dedicado.
- **Por quê:** isolar I/O facilita teste e evita timeout em request HTTP.

```python
# apps/payroll/services/folha.py
from django.db import transaction
from apps.payroll.tasks import gerar_eventos_esocial_da_folha

@transaction.atomic
def fechar_folha(folha):
    folha.status = "fechada"
    folha.save()
    transaction.on_commit(lambda: gerar_eventos_esocial_da_folha.delay(folha.id))
```

---

## 8. Composição de services

Service pode chamar outro service. Mas:

- ✅ Ok: `admitir_servidor` chama `criar_evento_auditoria(...)` (helper).
- ❌ Evite: cadeia funda (`A` chama `B` chama `C` chama `D`) sem necessidade clara — a regra fica difícil de seguir.
- **Toda composição roda na mesma transação** (atomic é reentrante, ok).

---

## 9. Testes

### Estrutura
```
apps/people/tests/
├── test_models.py
├── test_services_admissao.py
├── test_services_desligamento.py
└── ...
```

### Padrão de teste de service

```python
import pytest
from datetime import date
from decimal import Decimal

from apps.people.services.admissao import admitir_servidor, DadosAdmissao
from apps.people.services.exceptions import AdmissaoInvalidaError


@pytest.mark.django_db
class TestAdmitirServidor:
    def test_admite_servidor_com_dados_validos(self, municipio, cargo, lotacao):
        dados = DadosAdmissao(
            nome="João Silva",
            cpf="123.456.789-09",
            data_nascimento=date(1990, 1, 1),
            matricula="0001",
            cargo_id=cargo.id,
            lotacao_id=lotacao.id,
            regime="estatutario",
            data_admissao=date(2026, 1, 1),
            salario_base=Decimal("3500.00"),
        )
        servidor = admitir_servidor(municipio, dados)
        assert servidor.matricula == "0001"
        assert servidor.vinculos.count() == 1

    def test_falha_se_matricula_duplicada(self, municipio, servidor_existente, ...):
        with pytest.raises(AdmissaoInvalidaError) as exc:
            admitir_servidor(municipio, dados_com_mesma_matricula)
        assert exc.value.code == "MATRICULA_DUPLICADA"
```

### Regras
- **Cada caminho de exceção** tem teste dedicado.
- **Cada caminho feliz** tem teste dedicado.
- **Side-effects** (Celery task, `transaction.on_commit`) testados via mock ou `CELERY_TASK_ALWAYS_EAGER`.
- **Cobertura de service ≥ 90%** (são o coração do produto).

---

## 10. Tipagem

- **Type hints obrigatórios** em todo service.
- Para entidades de retorno complexas, usar **`@dataclass(frozen=True)`** (DTO imutável).
- Não retornar `dict` solto — sempre tipo nomeado.

```python
# bom
@dataclass(frozen=True)
class ResumoFolha:
    total_proventos: Decimal
    total_descontos: Decimal
    total_liquido: Decimal
    qtd_servidores: int

def calcular_folha(folha_id: int) -> ResumoFolha: ...

# ruim
def calcular_folha(folha_id):
    return {"total_proventos": ..., ...}
```

---

## 11. Logging em services

```python
import logging
logger = logging.getLogger(__name__)

def admitir_servidor(municipio, dados):
    logger.info(
        "admissao.iniciada",
        extra={"municipio_id": municipio.id, "matricula": dados.matricula},
    )
    # ...
    logger.info("admissao.concluida", extra={"servidor_id": servidor.id})
    return servidor
```

- Nome do evento em **dot.notation** (`admissao.iniciada`, `folha.fechada`).
- `extra` carrega contexto estruturado (vai para JSON em prod).
- **Nunca** logar dado sensível completo (CPF, conta).

---

## 12. Checklist antes de commitar service

- [ ] Função (ou classe se justificado), com type hints completos.
- [ ] `@transaction.atomic` em qualquer escrita multi-tabela.
- [ ] Validações cedo, com exceção de domínio (não `Exception` genérica).
- [ ] Side-effects via `transaction.on_commit` ou Celery task.
- [ ] Docstring explicando: o que faz, parâmetros, retorno, exceções.
- [ ] Teste de cada caminho (feliz e cada exceção).
- [ ] Cobertura ≥ 90% no arquivo do service.
- [ ] Entrada no `CHANGELOG.md`.
- [ ] `ruff check .` verde.
