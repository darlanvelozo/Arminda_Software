# Arminda

Sistema SaaS de folha de pagamento e gestão de pessoal para prefeituras brasileiras.

> Substituto moderno para sistemas legados (Fiorilli SIP e similares), com paridade funcional e experiência nativa para 2026: mobile, WhatsApp, BI e IA.

---

## Status

🟢 **Em produção** — https://arminda.site (Hostinger VPS, HTTPS, gunicorn + Nginx + systemd).

- **Versão atual:** `v0.23.0` (Onda 4.4b — folha exportável em PDF)
- **Bloco corrente:** Bloco 4 — Obrigações legais federais **em andamento** (eSocial: geração S-1000/S-1005/S-1010 + validação XSD, cofre de certificados A1 + assinatura digital). Bloco 3 concluído. Bloco 2 a 85% (2.7 desbloqueada — base real do SIP disponível)
- **Testes:** 523 backend (pytest) + 10 frontend (vitest) verdes
- **Painel público:** https://darlanvelozo.github.io/Arminda_Software/

O projeto está sendo construído em **11 blocos sequenciais** (0–10). Ver
[docs/ROADMAP.md](docs/ROADMAP.md) para o plano completo. Previsão de v1
completa: dez/2027.

---

## Stack

**Backend**
- Python 3.12 + Django 5 + Django REST Framework
- PostgreSQL 16 (multi-tenant por schema)
- Redis 7 + Celery (filas e cálculo assíncrono)
- pip + requirements.txt

**Frontend**
- Vite 5 + React 18 + TypeScript
- TailwindCSS + shadcn/ui
- TanStack Query (estado de servidor)
- React Router

**Infraestrutura**
- Docker Compose (dev local)
- GitHub Actions (CI)

Ver [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) para o racional das decisões.

---

## Estrutura do repositório

```
Arminda_Software/
├── backend/        Django + DRF — API e regras de negócio
├── frontend/       Vite + React — interface web do produto
├── status-page/    Painel público de acompanhamento (cliente)
├── docs/           Documentação (arquitetura, roadmap, ADRs, relatórios)
├── scripts/        Utilitários de dev (setup, importadores, etc.)
└── docker-compose.yml
```

**Painel de acompanhamento:** `https://darlanvelozo.github.io/Arminda_Software/`
Atualizado a cada entrega. Para editar, ver [status-page/README.md](status-page/README.md).

---

## Como rodar (dev local)

### Pré-requisitos

- Python 3.12+
- Node.js 20+
- Docker + Docker Compose
- Git

### 1. Clonar e configurar variáveis

```bash
git clone https://github.com/darlanvelozo/Arminda_Software.git
cd Arminda_Software
cp .env.example .env
```

### 2. Subir Postgres e Redis

```bash
docker compose up -d
```

### 3. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Linux/Mac
# .venv\Scripts\activate           # Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

API em `http://localhost:8000`. Admin em `http://localhost:8000/admin`.

### 4. Frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Interface em `http://localhost:5173`.

---

## Documentação

### Sistema de contexto (leitura obrigatória antes de implementar)

- **[CONTEXT.md](CONTEXT.md)** — contexto global do projeto (mestre)
- **[CHANGELOG.md](CHANGELOG.md)** — memória de todas as alterações
- **[backend/CONTEXT.md](backend/CONTEXT.md)** — regras do backend Django
  - [backend/CONTEXT_MODELS.md](backend/CONTEXT_MODELS.md) — camada de models
  - [backend/CONTEXT_SERVICES.md](backend/CONTEXT_SERVICES.md) — camada de services
  - [backend/apps/CONTEXT.md](backend/apps/CONTEXT.md) — estrutura interna de cada app
- **[frontend/CONTEXT.md](frontend/CONTEXT.md)** — regras do frontend React
  - [frontend/src/pages/CONTEXT.md](frontend/src/pages/CONTEXT.md) — páginas
  - [frontend/src/components/CONTEXT.md](frontend/src/components/CONTEXT.md) — componentes

### Documentação técnica

- **[CLAUDE.md](CLAUDE.md)** — instruções para Claude Code (leia antes de qualquer trabalho com IA neste repo)
- **[ROADMAP.md](docs/ROADMAP.md)** — os 11 blocos de construção (0–10) e o que cada um entrega
- **[PERSONAS.md](docs/PERSONAS.md)** — quem usa o sistema (matriz Persona × Bloco)
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** — visão arquitetural e decisões de stack
- **[CONTRIBUTING.md](docs/CONTRIBUTING.md)** — padrões de commit, branch e PR
- **[SETUP_NOVA_MAQUINA.md](docs/SETUP_NOVA_MAQUINA.md)** — checklist passo-a-passo para subir o projeto em máquina nova
- **[DEPLOY_PRODUCAO.md](docs/DEPLOY_PRODUCAO.md)** — runbook de deploy na VPS (arminda.site)
- **[MULTI_TENANT_PLAYBOOK.md](docs/MULTI_TENANT_PLAYBOOK.md)** — operação multi-tenant no dia-a-dia
- **[adr/](docs/adr)** — 17 Architecture Decision Records (decisões técnicas registradas)

---

## Contexto do projeto

O Arminda nasce para resolver um problema concreto: prefeituras brasileiras usam, hoje, sistemas de folha com arquitetura desktop, UX dos anos 2000 e dependência operacional do fornecedor (acessos remotos para qualquer ajuste). O Fiorilli SIP — concorrente principal — está em ~1.100 municípios e tem 21 anos de produto, com motor de cálculo robusto e cobertura legal completa, mas baixa modernidade.

A estratégia do Arminda **não é** competir no motor de cálculo (paridade é inegociável, mas não é diferencial). É competir em:

- UX moderna (web, mobile, PWA)
- Integrações nativas (WhatsApp, APIs públicas, bancos)
- BI em tempo real (dashboards, alertas, indicadores)
- IA aplicada (importador universal, alertas automáticos, simulador)
- Modelo SaaS multi-tenant (sem instalação local, atualizações automáticas)

Detalhes do diagnóstico do mercado e da análise técnica do concorrente estão na pasta `docs/`.

---

## Autor

Darlan Velozo · Teresina, PI
