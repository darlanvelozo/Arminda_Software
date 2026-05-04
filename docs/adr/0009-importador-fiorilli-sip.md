# ADR-0009 — Importador Fiorilli SIP (Firebird → Postgres)

**Status:** Aceita · 2026-04-30 · **Bloco 1.4**

## Contexto

O sistema legado das prefeituras-piloto é o **Fiorilli SIP**, que persiste em
Firebird 2.5 (`SIP.FDB`, ODS 11.2). Para o piloto rodar em paralelo (Bloco 6) e
para o município poder testar Arminda com dados reais antes do
fechamento de folha, precisamos importar:

1. **Cadastros** (MVP desta onda): Cargo, Lotação, Servidor, Vínculo Funcional,
   Dependente.
2. **Histórico financeiro** (depende do Bloco 2 — engine de cálculo): Eventos
   Fixos (1.387 linhas), Movimento (~250k linhas), Férias.

O diagnóstico do banco SIP do município de São Raimundo do Doca Bezerra/MA
(2026-04-30) mapeou as tabelas-chave e a volumetria. Esta ADR fixa a
estratégia técnica para o **MVP de cadastros** (item 1).

### Não-objetivos (intencionalmente fora do escopo)

- Migração reversa (Arminda → SIP). Direção é unidirecional.
- Sincronização incremental contínua. Importação é em "carga única" (com
  re-run idempotente para correção).
- Histórico financeiro/folha. Espera Bloco 2.

## Decisões

### 1. Biblioteca — `firebirdsql` (pure Python)

Existem três opções viáveis no Python:

| Lib | Tipo | Prós | Contras |
|---|---|---|---|
| `firebirdsql` | Pure Python | Sem deps nativas, instala via pip em qualquer SO | Wire protocol apenas (precisa server rodando) |
| `fdb` | Wrapper de `libfbclient` | Inclui modo embedded (sem server) | Precisa instalar libs nativas; abandonada (favoritou pyfirebird) |
| `firebird-driver` | Sucessor oficial | Suporta FB 3+ | Não suporta ODS 11.2 (FB 2.5) sem libs antigas |

**Decisão: `firebirdsql`.** SIP.FDB é ODS 11.2 (FB 2.5), que `firebirdsql`
suporta. Sem dependências nativas vira deploy mais simples (CI, dev, prod).
A contrapartida (precisar de um server FB rodando) é resolvida com Docker
(`jacobalberty/firebird:2.5-ss`) — o município passa o backup do FDB, a
gente sobe o container, importa, derruba.

A versão usada não fala TLS antigo do FB, então rodamos em rede privada/local
(porta exposta apenas no host do importador).

### 2. App `apps.imports` em `TENANT_APPS`

Cada município tem seu próprio histórico de importações; não faz sentido
compartilhar `SipImportRecord` entre tenants. Mora em `TENANT_APPS` para
que cada schema mantenha sua tabela isolada.

### 3. Pipeline ETL com 3 fases discretas

```
[FDB Firebird]
      │
      ▼ extract  (apps.imports.adapters.firebird)
{linhas: list[dict]}      ←— uma chamada SQL por entidade
      │
      ▼ transform (apps.imports.services.mapping)
{entities: list[ArmindaDict]}     ←— funções puras (testáveis sem DB)
      │
      ▼ load     (apps.imports.services.loaders.<entity>)
[Postgres tenant schema]  ←— update_or_create por chave SIP, em transação atômica
```

- **extract** não filtra nem transforma — só lê. Retorna dicts brutos.
- **transform** é puro: `def map_cargo_sip_to_arminda(row: dict) -> CargoDict`.
  Sem efeitos colaterais; permite teste sem mock complexo.
- **load** pega o dict transformado e chama `Cargo.objects.update_or_create(...)`
  com a chave SIP como `defaults`. Cada entidade tem um loader.

Vantagem: os 3 estágios são independentes. Se o mapeamento muda, não toca
no extract. Se a estrutura SIP muda em outro município, escrevemos outro
extract. O load fica intocado.

### 4. Idempotência por chave SIP estável

| Entidade Arminda | Chave SIP | Como guardamos |
|---|---|---|
| Cargo | `(EMPRESA, CODIGO)` | `Cargo.codigo = "001-PROFE"` (concatenado) |
| Lotação | `(EMPRESA, CODIGO)` em LOCAL_TRABALHO | `Lotacao.codigo = "001-LT-15"` |
| Servidor | `CPF` (já único em PESSOA) | `Servidor.cpf` |
| VinculoFuncional | `(EMPRESA, REGISTRO)` em TRABALHADOR | novo campo `matricula_contrato` |
| Dependente | `(servidor.cpf, nome, data_nascimento)` | composto natural |

`update_or_create(codigo=…, defaults={...})` torna o re-run idempotente:
rodar a importação 2x produz o mesmo estado final.

### 5. Modelo de auditoria — `SipImportRecord`

```python
class SipImportRecord(models.Model):
    tipo = CharField(choices=...)         # "cargo" | "lotacao" | ...
    chave_sip = CharField(max_length=120) # ex: "001-PROFE"
    arminda_id = PositiveIntegerField()
    importado_em = DateTimeField(auto_now_add=True)
    atualizado_em = DateTimeField(auto_now=True)
    payload_sip_hash = CharField(max_length=64)  # sha256 do dict bruto
    status = CharField(choices=["ok", "erro"])
    erro_mensagem = TextField(blank=True)
```

Permite:
- Saber se um registro foi importado (por chave SIP).
- Detectar se o payload mudou na origem (`payload_sip_hash` diferente do anterior).
- Rastrear erros por linha (por que a importação não atualizou X).

### 6. Política de erros — coletar, não falhar

Linhas com problema (CPF inválido, FK inexistente, etc.) **não interrompem
o batch**. São registradas em `SipImportRecord(status="erro")` com a
mensagem. No fim, o command imprime resumo:

```
Cargos:    91 lidos · 89 ok · 2 erros
Lotações:  66 lidos · 66 ok · 0 erros
Servidores: 517 lidos · 510 ok · 7 erros
...
Erros (7):
  - CPF inválido em PESSOA(CPF=12345678900)
  - PESSOA(CPF=...) sem TRABALHADOR
  ...
```

Permite o usuário decidir: corrige na origem e re-roda, ou aceita as perdas.

### 7. Dry-run mode

`--dry-run` roda extract + transform + load **dentro de uma transação que
faz rollback no fim**. Imprime o relatório completo sem persistir nada.
Padrão para a primeira execução em qualquer município novo.

### 8. Batch size 500

`update_or_create` em loop é lento (1 round-trip por linha). Para
servidores (517) e dependentes (303) está OK; para movimento (250k, fora
do MVP) precisará de bulk upsert. Por enquanto, `transaction.atomic` por
batch de 500 mantém o lock curto e o rollback granular.

### 9. Migrations adicionando campos faltantes (todas nullable)

Para receber dados ricos do SIP sem quebrar contratos atuais:

**Cargo:**
- `data_criacao` (DateField, null) — `CARGOS.DTCRIACAO`
- `data_extincao` (DateField, null) — `CARGOS.DTEXTINCAO`
- `vagas_total` (PositiveIntegerField, null) — `CARGOS.VAGACARGO + VAGAFUNCAO + VAGAEMPREGO`
- `dedicacao_exclusiva` (BooleanField, default=False)
- `atribuicoes` (TextField, blank)

**Servidor:**
- `nacionalidade` (CharField(2), blank) — `PESSOA.NACIONALIDADE`
- `raca` (CharField(1), blank) — `PESSOA.RACA`
- `nome_pai` (CharField(200), blank) — `PESSOA.NOMEPAI`
- `nome_mae` (CharField(200), blank) — `PESSOA.NOMEMAE`
- `instrucao` (CharField(2), blank) — `PESSOA.INSTRUCAO`

**VinculoFuncional:**
- `matricula_contrato` (CharField(20), blank) — `TRABALHADOR.REGISTRO`
- `tipo_admissao` (CharField(2), blank) — `TRABALHADOR.TIPOADMISSAO`
- `processo_admissao` (CharField(20), blank) — `TRABALHADOR.PROCESSO`

Todos os campos são opcionais; o frontend atual continua funcionando sem
preencher nenhum deles.

### 10. Management command `import_fiorilli_sip`

```bash
python manage.py import_fiorilli_sip \
  --tenant mun_sao_raimundo \
  --host 127.0.0.1 --port 13050 \
  --database /firebird/data/SIP.FDB \
  --user FSCSIP --password fscpw \
  --tabelas cargos,lotacoes,servidores \
  [--dry-run] [--batch-size 500] [--limit 100]
```

- `--tenant` é obrigatório; o command faz `with schema_context(tenant)` para
  garantir que escreve no schema certo.
- `--tabelas` permite rodar etapa por etapa.
- `--limit N` limita as N primeiras linhas (debug rápido).
- `--dry-run` faz rollback no fim.

### 11. Senha do FDB do município — não persiste

A senha do FDB (`FSCSIP/fscpw` no caso do município de teste) é informada
**no momento da execução** via flag `--password` ou env `SIP_PASSWORD`.
Não é guardada em settings, banco, ou qualquer arquivo. O município faz
o procedimento manualmente no host de importação.

## Consequências

### Positivas

- **Time-to-import baixo**: subindo container FB 2.5 + rodando o command
  basta para um município novo.
- **Re-run safe**: idempotência via `update_or_create` permite rodar
  quantas vezes precisar até zerar erros.
- **Diagnosticável**: cada erro tem linha + mensagem; usuário sabe o que
  corrigir na origem.
- **Não quebra nada**: todas as mudanças são aditivas (campos opcionais,
  app novo, model novo).

### Negativas

- **Acoplado a SIP Fiorilli específico.** Outras prefeituras usam outros
  sistemas (Betha, Govbr, etc.) — vão precisar de adapters próprios. Por
  isso o pipeline está separado em camadas: o adapter Firebird/SIP é
  trocável; mapping e loaders ficam.
- **Performance ainda não otimizada** para histórico (250k movimentos).
  Esse esforço fica para a Onda 1.4-bis ou Bloco 2.
- **Sensível à charset WIN1252 do SIP**. O conector retorna bytes/string
  conforme configuração; a gente força `charset="WIN1252"` no connect.

## Implementação

Estrutura final:

```
backend/apps/imports/
├── __init__.py
├── apps.py
├── models.py                              # SipImportRecord
├── adapters/
│   ├── __init__.py
│   └── firebird.py                        # extrai do FDB
├── services/
│   ├── __init__.py
│   ├── mapping.py                         # row SIP → dict Arminda (puro)
│   └── loaders/
│       ├── __init__.py
│       ├── cargos.py
│       ├── lotacoes.py
│       ├── servidores.py
│       ├── vinculos.py
│       └── dependentes.py
├── management/
│   └── commands/
│       └── import_fiorilli_sip.py
├── migrations/
└── tests/
    ├── test_mapping.py                    # puro, sem DB
    ├── test_loaders.py                    # com Postgres
    └── test_command.py                    # smoke do command
```

## Referências

- Diagnóstico do FDB SIP (2026-04-30): 1029 tabelas mapeadas, 15 críticas
  para o importador (vide CHANGELOG.md).
- ADR-0006 — Implementação multi-tenant.
- Commit das migrations (TBD).
