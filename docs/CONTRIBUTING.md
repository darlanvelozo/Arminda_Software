# Contribuindo com o Arminda

> Convenções deste repositório. Mesmo sendo solo no início, manter padrão evita retrabalho quando o time crescer.

---

## Antes de qualquer contribuição: sistema de contexto

Toda implementação deve passar pelo sistema de contexto distribuído do Arminda. **Antes** de codar:

1. Ler [`CONTEXT.md`](../CONTEXT.md) (raiz) — sempre.
2. Ler o `CONTEXT.md` do escopo onde você vai mexer:
   - Backend → [`backend/CONTEXT.md`](../backend/CONTEXT.md)
   - Frontend → [`frontend/CONTEXT.md`](../frontend/CONTEXT.md)
3. Ler o `CONTEXT.md` específico se for arquivo crítico:
   - `models.py` → [`backend/CONTEXT_MODELS.md`](../backend/CONTEXT_MODELS.md)
   - regra de negócio (`services/`) → [`backend/CONTEXT_SERVICES.md`](../backend/CONTEXT_SERVICES.md)
   - app inteiro Django → [`backend/apps/CONTEXT.md`](../backend/apps/CONTEXT.md)
   - componente → [`frontend/src/components/CONTEXT.md`](../frontend/src/components/CONTEXT.md)
   - página → [`frontend/src/pages/CONTEXT.md`](../frontend/src/pages/CONTEXT.md)

**Depois** de codar:

1. Atualizar [`CHANGELOG.md`](../CHANGELOG.md) com a entrada estruturada.
2. Atualizar o `CONTEXT.md` pertinente se a alteração mudou padrão, regra ou estrutura.
3. Criar/atualizar ADR em `docs/adr/` se a decisão for difícil de reverter.

> **PR sem entrada no `CHANGELOG.md` ou que viole regra de algum `CONTEXT.md` é bloqueado.**

---

## Branches

- `main` — produção. Sempre verde no CI. Nunca commitar direto.
- `develop` — integração. Branch de trabalho. CI tem que passar.
- `feature/<curto-descritivo>` — uma feature ou bloco. Ex: `feature/cadastro-servidor`.
- `fix/<curto-descritivo>` — correção. Ex: `fix/calculo-13-decimal`.
- `chore/<curto-descritivo>` — manutenção, infra, deps. Ex: `chore/upgrade-django-5-1`.
- `docs/<curto-descritivo>` — só documentação. Ex: `docs/adr-multi-tenant`.

Branches de feature saem de `develop`, voltam pra `develop`. `develop` → `main` é release.

---

## Commits — Conventional Commits

Formato: `<tipo>(<escopo opcional>): <descrição curta>`

**Tipos**
- `feat` — nova feature
- `fix` — correção
- `refactor` — mudança sem alterar comportamento
- `chore` — manutenção (deps, build, configs)
- `docs` — documentação
- `test` — adiciona ou ajusta testes
- `style` — formatação, whitespace
- `perf` — melhoria de performance
- `ci` — mudanças em pipelines

**Exemplos**
```
feat(people): adiciona cadastro de servidor com validação de CPF
fix(payroll): corrige arredondamento no cálculo de INSS
chore(deps): atualiza django para 5.1.4
docs(adr): adiciona ADR-0005 sobre engine de cálculo
```

Mensagens em **português** (cliente é brasileiro, time futuro provavelmente também). Imperativo, primeira letra minúscula, sem ponto final.

---

## Pull Requests

- Sempre via PR para `develop` (e de `develop` para `main` em release).
- Use o template de PR — ele está em `.github/pull_request_template.md`.
- CI tem que passar antes do merge.
- PRs grandes (>500 linhas) devem ser quebrados, salvo exceções documentadas no PR.

### Template de descrição
1. **O quê** — o que muda neste PR
2. **Por quê** — motivação / referência ao bloco do roadmap
3. **Como testar** — passos para validar localmente
4. **Checklist** — itens que se aplicam (testes, docs, migrations)

---

## Estilo de código

### Backend (Python)
- Formatação: **ruff format** (substitui black + isort).
- Linter: **ruff check**.
- Type hints obrigatórios em funções públicas e modelos.
- Strings em português para mensagens de UI; código (variáveis, classes) em inglês.

```bash
cd backend
ruff format .
ruff check .
```

### Frontend (TypeScript)
- Formatação: **prettier** (config no repo).
- Linter: **eslint** com preset typescript-react.
- Componentes em PascalCase, hooks com prefixo `use`.

```bash
cd frontend
npm run lint
npm run format
```

---

## Testes

- Backend: **pytest + pytest-django**. Mínimo 80% de cobertura nas regras de domínio (apps `people`, `payroll`, `reports`).
- Frontend: **vitest + testing-library**. Cobertura de componentes críticos e hooks.
- Cada PR de feature deve trazer testes; cada bug fix deve trazer um teste que reproduz o bug.

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```

---

## Migrations Django

- Sempre revisar a migration gerada antes de commitar.
- Nomes descritivos: `python manage.py makemigrations --name adiciona_campo_cbo_em_cargo`.
- Migrations destrutivas (drop column, rename) precisam de plano de rollback documentado no PR.

---

## Versionamento e releases

A política completa está em [`docs/adr/0010-versionamento-e-releases.md`](adr/0010-versionamento-e-releases.md). Resumo operacional:

**Esquema:** `MAJOR.MINOR.PATCH` adaptado ao roadmap por blocos.
- `MAJOR=0` enquanto pré-piloto · vira `1` quando a folha calcular (fim do Bloco 2) · vira `2` quando o piloto encerrar (Bloco 6).
- `MINOR` avança a cada bloco/onda que entrega feature visível.
- `PATCH` avança em correções e polimentos dentro da mesma onda.

**Toda onda fecha com 6 passos:**

1. Commit final em `main` com CI verde.
2. `CHANGELOG.md` com a entrada estruturada da onda.
3. `status-page/status.json` atualizado (progresso + changelog visível ao stakeholder).
4. `frontend/src/pages/GuiaPage.tsx` atualizado se a feature mudou o que o operador vê (lembre do `LAST_UPDATED`).
5. **Tag anotada** com a mensagem padronizada — ver template na ADR-0010 §3.
6. `git push origin main && git push origin <tag>`.

**Relatório quinzenal:** a cada 15 dias, publicar um HTML em `status-page/relatorios/<YYYY-MM-DD>-quinzenal-NN.html` com o consolidado da quinzena, e adicionar entrada no array `relatorios` do `status.json`. Próximos: 22/05/2026, 05/06/2026, e assim por diante.

**Não fazer:** tag leve (use sempre `git tag -a`), back-port em branches de manutenção (suba PATCH na corrente — ver §5 da ADR).

---

## ADRs (Architecture Decision Records)

Decisões técnicas relevantes vão em `docs/adr/`. Use o template existente. Resumo:

- Numeração sequencial: `0001-`, `0002-`, etc.
- Status: Proposto → Aceito → Substituído por XXXX
- Estrutura: Contexto, Decisão, Consequências.

Quando criar um ADR? Quando a decisão **vai influenciar futuras decisões** ou **é difícil de reverter**.

---

## Segurança e dados sensíveis

- **Nunca** commitar `.env`, dados de servidores reais, dumps de banco.
- Dados de teste são fictícios (faker em Python, faker.js no frontend).
- Bases reais do Fiorilli ficam **fora do repo**, em volume Docker ou pasta ignorada.

---

## Quando em dúvida

Documente a dúvida num issue ou ADR. Decisão escrita > decisão na cabeça de uma pessoa só.
