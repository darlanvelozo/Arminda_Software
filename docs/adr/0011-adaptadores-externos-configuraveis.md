# ADR-0011 — Adaptadores externos configuráveis no admin Django

**Status:** Aceita · 2026-05-10 · Vigora para Blocos 4, 5 e 7

## Contexto

O Arminda é um produto multi-município. Cada prefeitura brasileira tem
um conjunto **diferente** de obrigações de envio para órgãos externos,
e esse conjunto depende:

- **Do estado** — TCE-MA, TCE-PB (Sagres), TCE-SP (Audesp), TCE-PE,
  TCE-CE, etc. Cada um com layout próprio.
- **Do porte** — municípios pequenos não enviam Audesp; alguns ainda
  geram SEFIP enquanto outros já estão 100% no eSocial.
- **Da pessoa jurídica** — o município tem múltiplos órgãos emissores
  com CNPJs próprios (Prefeitura, Fundo de Saúde, Fundo de Assistência
  Social, Câmara) e cada um pode ter obrigações diferentes (ex.: a
  Câmara não envia eSocial pelo CNPJ da Prefeitura).

O Bloco 5 do roadmap já dizia "Framework de adaptadores extensível
para outros TCEs", mas faltava decidir **onde mora a configuração de
quem está ativo e para qual entidade**.

Durante a análise de um MANAD de 2020 (Fundo Municipal de Assistência
Social de Canindé de São Francisco/SE — CNPJ próprio, 159 servidores)
ficou claro que **a configuração precisa ser por (município × órgão
emissor × tipo de integração)**, não apenas por município.

### Não-objetivos

- Sistema de plugins externos via PyPI ou diretório dinâmico — todo
  adapter mora no monorepo, sob controle de versão.
- Editor visual de layouts (drag-and-drop). Layout é decidido em
  código.

## Decisão

### 1. Tabela `IntegracaoExterna` em `apps.core` (SHARED)

```python
class TipoIntegracao(TextChoices):
    ESOCIAL    = "esocial",    "eSocial"
    MANAD      = "manad",      "MANAD"
    SEFIP      = "sefip",      "SEFIP"
    CAGED      = "caged",      "CAGED"
    RAIS       = "rais",       "RAIS"
    DIRF       = "dirf",       "DIRF"
    DCTFWEB    = "dctfweb",    "DCTFWeb"
    TCE_MA     = "tce_ma",     "TCE-MA (SACOP/SIGFIS)"
    TCE_PB     = "tce_pb",     "TCE-PB (Sagres Folha)"
    TCE_SP     = "tce_sp",     "TCE-SP (Audesp)"
    # ... outros estados conforme demanda

class IntegracaoExterna(models.Model):
    municipio = ForeignKey(Municipio)
    orgao_emissor = ForeignKey(OrgaoEmissor)  # CNPJ que envia
    tipo = CharField(choices=TipoIntegracao.choices)
    ativo = BooleanField(default=True)
    configuracao = JSONField(default=dict)
        # endpoint, certificate_id, layout_version,
        # ambiente (homologacao/producao), credenciais_cifradas
    criado_em = DateTimeField(auto_now_add=True)
    atualizado_em = DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("municipio", "orgao_emissor", "tipo")]
```

Vive em `SHARED_APPS` (schema `public`) porque a equipe Arminda
(staff_arminda) precisa ver de fora a configuração de todos os
municípios para suporte/diagnóstico.

### 2. Adapter Pattern em código

Cada `tipo` tem um adapter no diretório
`apps/<bloco>/adapters/<tipo>.py` implementando interface comum:

```python
class IntegracaoAdapter(Protocol):
    def gerar_remessa(self, competencia: date, contexto: ContextoFolha) -> Remessa:
        """Constrói o arquivo/payload (sem enviar)."""

    def validar(self, remessa: Remessa) -> ValidacaoResult:
        """Checks estruturais antes do envio."""

    def enviar(self, remessa: Remessa, integracao: IntegracaoExterna) -> EnvioResult:
        """Envia ao endpoint configurado em `integracao.configuracao`."""

    def consultar_status(self, envio: Envio) -> StatusResult:
        """Reconciliação posterior."""
```

Registro central em `apps.core.integracoes.registry`:

```python
ADAPTERS: dict[str, type[IntegracaoAdapter]] = {
    "esocial": ESocialAdapter,
    "manad":   ManadAdapter,
    "tce_ma":  TCEMaranhaoAdapter,
    "tce_pb":  TCEParaibaSagresAdapter,
    # ...
}
```

### 3. Admin Django expõe a tabela

`apps.core.admin.IntegracaoExternaAdmin` permite ao staff_arminda
configurar por município:

- Ativar/desativar uma integração
- Editar JSON de configuração (endpoint, ambiente, credenciais)
- Visualizar logs de envio (linkado para `Envio`)

Em produção, **credenciais ficam cifradas** (Fernet com chave do env)
no JSON antes de persistir — never plain in DB.

### 4. Frontend monta menu dinamicamente

Endpoint `GET /api/core/integracoes/ativas/` retorna lista de tipos
ativos para o tenant atual:

```json
[
  {"tipo": "esocial", "label": "eSocial", "rota": "/relatorios/esocial"},
  {"tipo": "manad",   "label": "MANAD",   "rota": "/relatorios/manad"},
  {"tipo": "tce_pb",  "label": "Sagres Folha (TCE-PB)", "rota": "/tribunal/tce-pb"}
]
```

O Sidebar do frontend lê essa lista e renderiza os ícones de menu
correspondentes — município que não usa Sagres não vê o ícone.

### 5. Entidade `OrgaoEmissor` em `apps.people` (TENANT)

```python
class OrgaoEmissor(TimeStampedModel):
    nome = CharField(max_length=200)        # "Fundo Municipal de Assistência Social"
    sigla = CharField(max_length=20)         # "FMAS"
    cnpj = CharField(max_length=18)          # único por tenant
    eh_principal = BooleanField(default=False)  # 1 marca a Prefeitura matriz
    ativo = BooleanField(default=True)
```

Relacionamento com `UnidadeOrcamentaria`:
- `UnidadeOrcamentaria.orgao_emissor` (FK nullable) — quem é o
  emissor responsável pelo empenho de cada unidade.
- Permite agrupar unidades pelo CNPJ emissor para gerar MANAD/eSocial.

### 6. Auditoria

Toda mudança em `IntegracaoExterna` fica em `simple-history`. Toda
geração de remessa cria `Envio(integracao, competencia, payload_hash,
status, retorno, criado_por)`. Operador ou staff sabe exatamente o
que foi enviado, quando, por quem.

### 7. Ordem de implementação no roadmap

| Bloco | Adapter | Quando |
|---|---|---|
| 4 | `OrgaoEmissor` + `IntegracaoExterna` (tabela) + `ESocialAdapter` | Out-Nov/2026 |
| 4 | `ManadAdapter`, `SefipAdapter`, `CagedAdapter`, `RaisAdapter`, `DirfAdapter` | Out-Nov/2026 |
| 5 | `TCEMaranhaoAdapter`, `TCEParaibaSagresAdapter` | Dez/2026 |
| 5 | Endpoint `/api/core/integracoes/ativas/` + UI do menu dinâmico | Dez/2026 |
| 7 | Outros TCEs (SP/Audesp, PE, CE, etc.) sob demanda | Fev-Abr/2027 |
| 7 | Importadores universais (Betha, Govbr, Implanta, etc.) seguem o mesmo padrão de adapter | Fev-Abr/2027 |

## Consequências

### Positivas

- **Multi-município de verdade:** uma instância do Arminda atende
  prefeituras com perfis fiscais completamente diferentes sem deploy
  de código.
- **Diferenciação por órgão emissor:** o MANAD do Fundo de Saúde e o
  MANAD da Prefeitura matriz são gerados separados, cada um com seu
  CNPJ — como exige a Receita.
- **Suporte mais fácil:** staff_arminda vê todas as configurações no
  admin, sem precisar `psql` no banco.
- **Frontend sem item-fantasma:** município que não usa Sagres
  literalmente não vê o ícone — reduz fricção visual e ligações de
  suporte ("o que é esse botão aqui?").

### Negativas

- **Mais um modelo central em `apps.core`** + 1 modelo em
  `apps.people` (OrgaoEmissor). Migração ao adicionar é fácil; a
  complexidade vem em modelar o JSON de `configuracao` (decidir o
  shape por tipo).
- **Credenciais em JSON cifrado** exige rotina de rotação de chave
  Fernet — operação manual a cada N anos.
- **Adapters precisam de testes E2E contra sandbox de produção** dos
  órgãos — alguns sandboxes são instáveis e fora do nosso controle.

## Implementação imediata (esta onda)

**Nada.** Esta ADR documenta a decisão arquitetural para que o Bloco
4 e o Bloco 5 sejam desenhados pensando multi-prefeitura desde o
início. A implementação efetiva começa no **Bloco 4 (Out-Nov/2026)**.

Por enquanto, esta ADR existe para:
1. Garantir que ninguém implemente eSocial ou TCE no caminho
   "monolítico" (uma tabela `Configuracao` global, hardcoded para um
   município).
2. Servir de referência ao adicionar tipos novos
   (`TCEParaibaSagresAdapter` por exemplo).

## Referências

- ADR-0006 — Multi-tenant por schema (base da separação por município).
- ADR-0009 — Importador Fiorilli SIP (já segue padrão Adapter
  similar; este ADR generaliza).
- ADR-0010 — Versionamento (cada adapter novo é PATCH ou MINOR
  conforme escopo).
