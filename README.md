# Arminda

Sistema SaaS de folha de pagamento e gestão de pessoal para prefeituras brasileiras.

> Substituto moderno para sistemas legados (Fiorilli SIP e similares), com paridade funcional e experiência nativa para 2026: mobile, WhatsApp, BI e IA.

---

## Status

🟡 **Bloco 0 — Estrutura inicial** (em andamento)

O projeto está sendo construído em blocos sequenciais. Ver [docs/ROADMAP.md](docs/ROADMAP.md) para o plano completo.

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

- **[ROADMAP.md](docs/ROADMAP.md)** — os 7 blocos de construção e o que cada um entrega
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** — visão arquitetural e decisões de stack
- **[CONTRIBUTING.md](docs/CONTRIBUTING.md)** — padrões de commit, branch e PR
- **[adr/](docs/adr)** — Architecture Decision Records (decisões técnicas registradas)

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
