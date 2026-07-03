# CLAUDE.md — Instruções para Claude Code

> Este arquivo é lido automaticamente pelo Claude Code ao abrir o repo.
> Mantém o próximo Claude (você ou outro, em qualquer máquina) alinhado
> sem precisar reconstruir contexto do zero.
>
> **Mensagens, commits, comentários, docs, UI: tudo em português.**
> Apenas identificadores de código (variáveis/funções/classes) ficam
> em inglês — exceto domínio brasileiro intraduzível (`Servidor`,
> `Lotacao`, `cpf`, `pis_pasep`).

---

## 1. Estado atual do projeto

**Arminda** é um SaaS multi-tenant de **folha de pagamento e gestão
de pessoal para prefeituras brasileiras**. Substitui Fiorilli SIP e
similares com paridade legal + UX moderna + multi-tenant nativo.

- **Versão atual:** `v0.20.0` (Onda 4.3 — eSocial: natureza de rubrica + S-1010)
- **Bloco corrente:** **Bloco 4 — Obrigações legais federais: em andamento (~20%)** — eSocial: S-1000/S-1005 (4.1) + natureza de rubrica (Tabela 3) e S-1010 (4.3), geração de XML validada contra o XSD oficial S-1.3. Bloco 3 concluído. Bloco 2 a 85% (a 2.7 está desbloqueada — base real do SIP disponível)
- **Produção:** https://arminda.site (Hostinger VPS, HTTPS válido, Postgres dedicado, gunicorn + Nginx + systemd)
- **Painel público:** https://darlanvelozo.github.io/Arminda_Software/ (GitHub Pages, atualiza via push em `main`)
- **Testes:** 512 backend (pytest) + 10 frontend (vitest), todos verdes
- **Repositório:** público no GitHub — **não commitar secrets** sob nenhuma hipótese
- **Roadmap:** 11 blocos (0–10), previsão de v1 completa em dez/2027 (ver [docs/ROADMAP.md](docs/ROADMAP.md))

Próximos passos naturais (Bloco 4): assinatura digital dos eventos (XML-DSig,
certificado ICP-Brasil) e transmissão ao governo; e os demais eventos eSocial
(S-1010, S-1020, S-2200, S-1200…). Em paralelo, a **2.7** (paridade Fiorilli)
fecha o Bloco 2 quando houver dados do SIP. Dívida do Bloco 3: folha
complementar **modo acumulado** (via `Folha.folha_origem` — ADR-0019).
Ver [CHANGELOG.md](CHANGELOG.md).

> **Onde você está rodando (desde 30/05/2026):** o desenvolvimento acontece
> **na própria VPS**, em `/opt/arminda-dev` (banco `arminda_dev`, `.env` de dev,
> `runserver` manual na porta **8010**). **Nunca desenvolva em `/opt/arminda`** —
> aquele é o checkout que serve a produção (`arminda-backend.service`, gunicorn
> na 8001, banco `arminda_prod`). Detalhes em
> [docs/SETUP_NOVA_MAQUINA.md](docs/SETUP_NOVA_MAQUINA.md) (seção 0).

---

## 2. Onde ler primeiro (em ordem)

1. **[CONTEXT.md](CONTEXT.md)** — contexto global, estrutura, padrões transversais
2. **[docs/ROADMAP.md](docs/ROADMAP.md)** — os 11 blocos e o que cada um entrega
3. **[docs/PERSONAS.md](docs/PERSONAS.md)** — quem usa o sistema (matriz Persona × Bloco)
4. **[CHANGELOG.md](CHANGELOG.md)** — memória do projeto, toda alteração registrada
5. **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** — racional das decisões de stack
6. **[docs/adr/](docs/adr/)** — 21 ADRs (decisões formais)
7. **CONTEXT.md específicos** quando for mexer:
   - Backend: [backend/CONTEXT.md](backend/CONTEXT.md) → [`_MODELS`](backend/CONTEXT_MODELS.md) → [`_SERVICES`](backend/CONTEXT_SERVICES.md) → [`apps/CONTEXT.md`](backend/apps/CONTEXT.md)
   - Frontend: [frontend/CONTEXT.md](frontend/CONTEXT.md) → [`pages/CONTEXT.md`](frontend/src/pages/CONTEXT.md) → [`components/CONTEXT.md`](frontend/src/components/CONTEXT.md)

Pra rodar local em máquina nova: **[docs/SETUP_NOVA_MAQUINA.md](docs/SETUP_NOVA_MAQUINA.md)**.

Pra fazer deploy em produção: **[docs/DEPLOY_PRODUCAO.md](docs/DEPLOY_PRODUCAO.md)**.

---

## 3. Regras de processo (não negociáveis)

Estas regras vêm da experiência operacional com o usuário e estão
validadas. Toda nova entrega segue elas:

### 3.1 Validação integral antes de toda atualização
Antes de qualquer commit que vire release (tag), rodar a rotina completa:

```bash
# Backend
cd backend
.venv/bin/ruff check apps/
DJANGO_SETTINGS_MODULE=arminda.settings.dev .venv/bin/python manage.py check
DJANGO_SETTINGS_MODULE=arminda.settings.dev .venv/bin/python -m pytest -q

# Frontend
cd frontend
npm run lint
npx tsc --noEmit
npx vitest run
npm run build
```

Tudo precisa estar verde. O resultado vira entrada `tipo="validacao"` no
[`status-page/status.json`](status-page/status.json) **antes** da entrada
`tipo="entrega"` que ela valida.

### 3.2 Guias vivos sempre atualizados
Toda entrega que afeta a UX final atualiza **dois arquivos**:
- [`frontend/src/pages/GuiaPage.tsx`](frontend/src/pages/GuiaPage.tsx) — guia operacional do usuário final
- [`frontend/src/pages/GuiaAdminPage.tsx`](frontend/src/pages/GuiaAdminPage.tsx) — guia técnico para devs/admins

Lembre de atualizar `LAST_UPDATED` no topo de cada um. Se o guia ficar
defasado em relação ao que está em produção, é regressão.

### 3.3 Status page fala da aplicação, não de terceiros
No [`status-page/status.json`](status-page/status.json), os campos
`resumo_executivo` e `descricao` das entradas do changelog **nunca**
citam pessoas externas por nome ou papel (cliente, doutor, secretário,
etc.). O resumo é sobre o que a aplicação ganhou, não sobre
quem motivou. Esta regra é firme.

### 3.4 Sempre commitar por versão
Toda entrega (onda ou bloco) gera:
1. Commit com mensagem detalhada explicando o que mudou e por quê
2. Tag anotada `git tag -a vX.Y.Z -m "..."` (ADR-0010)
3. Entrada no [`CHANGELOG.md`](CHANGELOG.md)
4. Entrada no [`status-page/status.json`](status-page/status.json)
5. Push para `origin/main` + push de tags

### 3.5 Sem mocks de banco em testes
django-tenants exige conexão real para troca de schema. Testes de view
usam `APIClient` com token JWT + header `X-Tenant`. Testes de serviço
batem no Postgres real via `conftest.py`. Nunca mockar `Model.objects`.

### 3.6 Bug fix exige teste de regressão
Toda correção entra com um teste que reproduz o bug original. Se o
teste não roda ou não falha sem o fix, ele não está cumprindo o papel.

---

## 4. Comandos essenciais

### Backend
```bash
cd backend && source .venv/bin/activate

# Dev
DJANGO_SETTINGS_MODULE=arminda.settings.dev python manage.py runserver
DJANGO_SETTINGS_MODULE=arminda.settings.dev python manage.py migrate
DJANGO_SETTINGS_MODULE=arminda.settings.dev python manage.py createsuperuser

# Testes + lint
ruff check apps/
ruff format apps/
DJANGO_SETTINGS_MODULE=arminda.settings.dev python -m pytest -q
DJANGO_SETTINGS_MODULE=arminda.settings.dev python -m pytest apps/people/tests/test_X.py -v

# Gerar OpenAPI schema (regenerar tipos TS depois)
DJANGO_SETTINGS_MODULE=arminda.settings.dev python manage.py spectacular --file openapi-schema.json
```

### Frontend
```bash
cd frontend

# Dev
npm run dev                          # vite em :5173
npm run build                        # produção em dist/
npm run preview                      # serve o build

# Validação
npm run lint
npx tsc --noEmit
npx vitest run

# Tipos (precisa do backend rodando ou OpenAPI offline)
npm run gen:types                    # vai em http://localhost:8000/api/schema/
npm run gen:types:offline            # usa ./openapi-schema.json
```

### Status page (público, GH Pages)
```bash
cd status-page
python3 -m http.server 8765          # smoke local
# Editar status.json + assets/script.js + assets/styles.css
# Push em main → GH Pages atualiza em ~30s
```

### Deploy em produção
```bash
# Local
git push origin main && git push origin vX.Y.Z

# Na VPS (autorizado caso a caso)
ssh arminda-vps "sudo /opt/arminda/deploy/deploy.sh"
```

Ver [docs/DEPLOY_PRODUCAO.md](docs/DEPLOY_PRODUCAO.md) pra runbook completo.

---

## 5. Convenções de código (resumo)

Detalhes em cada `CONTEXT.md` específico. O essencial:

**Geral**
- Documentação/UI/commits/comentários: **português**
- Identificadores de código: **inglês** (exceto domínio BR intraduzível)
- Sem comentários óbvios — só comentar quando o **porquê** não é evidente
- Decimal sempre `quantize`-ado em valores financeiros

**Backend**
- Lógica de negócio em `apps/<app>/services/` (NÃO em views/viewsets)
- Models em `apps/<app>/models.py` — auditoria via `simple-history`
- `select_related`/`prefetch_related` em querysets que atravessam FK
- Multi-tenant: `from django_tenants.utils import schema_context` para
  operar em outro tenant; middleware roteia por `X-Tenant` header

**Frontend**
- TanStack Query para estado de servidor (não useState/useEffect para fetch)
- Tipos vêm do OpenAPI via `openapi-typescript` (ADR-0008)
- shadcn/ui via CLI (`npx shadcn@latest add <componente>`) — nunca manual
- Imports com alias `@/` (não relativo profundo)

**Git**
- Conventional Commits em português: `feat(payroll): adiciona X`
- `feat`/`fix`/`refactor`/`chore`/`docs`/`test`/`perf`/`ci`
- Marcar `⚠ BREAKING` quando muda contrato de API ou semântica
- Co-author no commit: `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`

---

## 6. Decisões fechadas (não revisitar)

Estas ADRs já estão aceitas e implementadas. Reabrir só com motivo forte:

| ADR | Decisão |
|---|---|
| 0001 | Monorepo (backend + frontend juntos) |
| 0002 | Django + DRF |
| 0003 | Vite + React + TypeScript + Tailwind + shadcn/ui |
| 0004/0006 | Multi-tenant por schema via `django-tenants`, roteamento por header `X-Tenant` |
| 0005 | User customizado (`apps.core.User`) com login por e-mail |
| 0007 | JWT + RBAC escopado por município, 5 papéis (`staff_arminda`, `admin_municipio`, `rh_municipio`, `financeiro_municipio`, `leitura_municipio`) |
| 0008 | Tipos TS via `openapi-typescript` |
| 0009 | Importador Fiorilli SIP (Firebird → Postgres) com pipeline ETL idempotente |
| 0010 | Versionamento `MAJOR.MINOR.PATCH` (MAJOR = bloco, MINOR = onda) |
| 0011 | Adaptadores externos configuráveis via admin (`OrgaoEmissor`, `IntegracaoExterna`) |
| 0012 | DSL de fórmulas via Python AST whitelist (sem `eval`/`exec`) |
| 0013 | Incidências automáticas (bases por flag) + RPPS por-tenant + cálculo em duas fases |
| 0014 | Holerite: JSON estruturado + PDF via ReportLab |
| 0015 | 13º salário: escopo de rubrica por tipo de folha (`tipos_folha`) + avos |
| 0016 | Rescisão: motivo no vínculo + verbas com gating por motivo |
| 0017 | Férias: programação por `FeriasItem` na folha + abono pecuniário |
| 0018 | Licença-prêmio: indenização por `LicencaPremioItem` (verba indenizatória) |
| 0019 | Folha complementar: lançamentos explícitos (`ComplementarItem`), `folha_origem` como gancho do modo acumulado |
| 0020 | eSocial: app `esocial`, modelo genérico `EventoESocial`, geração XML + validação XSD oficial (S-1.3); assinatura/transmissão depois |
| 0021 | Lições da base real Fiorilli: snapshot de incidência, natureza de rubrica (Tabela 3), `ResumoFolha`/BASES, S-1202 RPPS; base bruta fora do git (PII) |

Papéis novos a criar (mapeados em [PERSONAS.md](docs/PERSONAS.md)):
`gestor_municipio` (Bloco 7), `contador_municipio` (Bloco 9),
`controle_interno_municipio` (Bloco 10), `servidor_final` (Bloco 7).
Cada um vira ADR 0013+ antes de migration.

---

## 7. O que **NÃO** fazer

- ❌ Lógica de negócio em views/viewsets — sempre em `services/`
- ❌ `eval`, `exec`, ou execução de string como código (DSL já tem sandbox próprio)
- ❌ Commit de `.env` real, dump de banco real, base do Fiorilli
- ❌ `--no-verify` em commits, force-push em `main`
- ❌ Tag leve (`git tag X`); sempre `git tag -a X -m "..."`
- ❌ Mocks de `Model.objects` em testes (django-tenants exige DB real)
- ❌ Citar terceiros por nome/papel em `status.json` (regra 3.3)
- ❌ Componente shadcn/ui criado manualmente — sempre via CLI
- ❌ Imports relativos profundos (`../../../`)

---

## 8. Em caso de bug ou regressão

Procedimento:
1. Reproduzir local. Se não reproduz, escrever teste que reproduz.
2. Consultar [CHANGELOG.md](CHANGELOG.md) — o que mudou recentemente na área?
3. Consultar `CONTEXT.md` específico — alguma regra foi violada?
4. Corrigir, escrever teste de regressão, atualizar `CHANGELOG.md`.
5. Se causa raiz é falta de regra: adicionar regra no `CONTEXT.md` correspondente.

---

## 9. Quando começar uma nova onda

1. Ler o bloco no [ROADMAP.md](docs/ROADMAP.md) pra entender o escopo
2. Ler [PERSONAS.md](docs/PERSONAS.md) pra saber quem é afetado
3. Quebrar em tarefas via TodoWrite
4. Implementar backend primeiro (modelos → services → views → serializers → testes)
5. Frontend depois (tipos → queries → componentes → páginas → rotas → menu)
6. Atualizar guias vivos (`GuiaPage.tsx` + `GuiaAdminPage.tsx`)
7. Rodar validação integral (seção 3.1)
8. Atualizar `CHANGELOG.md` + `status-page/status.json`
9. Commit + tag anotada + push

---

## 10. Próximos passos sugeridos (memo)

Se estiver retomando o projeto:

- **Bloco 3 — concluído** (13º, rescisão, férias, licença-prêmio, complementar)
- **Bloco 4 — em andamento** (4.1: S-1000/S-1005; 4.3: natureza de rubrica +
  S-1010). Próximas ondas (reordenadas por ADR-0021):
  **4.4 — snapshot de incidência ao fechar folha + `ResumoFolha`/BASES**;
  **4.5 — periódicos S-1200 + S-1202 (RPPS) + S-1210**; **4.2 — cofre de
  certificados A1** (fundação de assinatura/transmissão e da integração
  Receita); depois **assinatura** (XML-DSig) e **transmissão**.
- **Bloco 10 — novo item mapeado:** monitoramento fiscal na Receita
  (intimações no e-CAC/DTE, prazos de recurso, malha fiscal) por prefeitura —
  depende do cofre de certificados (4.2) + canal SERPRO (Integra Contador/DTE)
- **Onda 2.7 — Testes de paridade contra Fiorilli** (fecha Bloco 2) —
  **desbloqueada**: base real do SIP (São João Batista-MA) disponível em
  `/opt/sip-bases` (fora do git); uso PII-safe (ADR-0021)
- Dívida do Bloco 3: folha complementar **modo acumulado** (recálculo delta +
  incidência sobre a base do mês, via `Folha.folha_origem` — ADR-0019)

> eSocial: os XSDs oficiais S-1.3 estão em `backend/apps/esocial/schemas/`.
> A validação relaxa só o `ds:Signature` (entra na onda de assinatura).
> `lxml` é dependência nova — `pip install -r requirements.txt` no deploy.

Bug pendente conhecido: nenhum.

---

## 11. Para o próximo Claude

- Este projeto tem uma documentação **muito rica** (5800+ linhas em
  `docs/` + `CONTEXT.md`s). Leia o pertinente antes de pedir contexto.
- O usuário valoriza: precisão, validação integral, commits limpos,
  prosa concisa em português, e nada de marketing nas docs internas.
- Quando em dúvida sobre escopo arquitetural, abra ADR antes de
  implementar — não decida sozinho coisa difícil de reverter.
- A página de status pública é vitrine — qualquer mudança lá deve
  passar por consideração visual (tem `prefers-reduced-motion`,
  responsivo, GH Pages).
- Em produção: NÃO rodar deploy sem autorização explícita do usuário
  na conversa atual. Acesso à VPS é via SSH (`arminda-vps` no
  `~/.ssh/config`), mas comandos de deploy passam por confirmação.
