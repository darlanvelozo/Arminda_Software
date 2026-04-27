# Contribuindo com o Arminda

> Convenções deste repositório. Mesmo sendo solo no início, manter padrão evita retrabalho quando o time crescer.

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
