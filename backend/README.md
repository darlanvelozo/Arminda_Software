# Backend — Arminda

API Django + DRF para o sistema Arminda.

## Estrutura

```
backend/
├── arminda/              # configuração do projeto Django
│   ├── settings/
│   │   ├── base.py       # configurações compartilhadas
│   │   ├── dev.py        # override para desenvolvimento
│   │   └── prod.py       # override para produção
│   ├── urls.py           # rotas raiz da API
│   ├── wsgi.py
│   └── asgi.py
├── apps/                 # apps Django (domínio)
│   ├── core/             # tenant, auth, RBAC
│   ├── people/           # servidores, cargos, vínculos
│   ├── payroll/          # folha, rubricas, cálculo
│   └── reports/          # relatórios e dashboards
├── tests/                # testes globais e fixtures
├── manage.py
├── requirements.txt
└── pyproject.toml        # config ruff + pytest + coverage
```

## Setup

```bash
# 1. Virtual env
python -m venv .venv
source .venv/bin/activate     # Linux/Mac
# .venv\Scripts\activate      # Windows

# 2. Dependências
pip install -r requirements.txt

# 3. .env (copiar da raiz do repo)
# já deve estar criado em ../.env

# 4. Migrations
python manage.py migrate

# 5. Superuser
python manage.py createsuperuser

# 6. Rodar
python manage.py runserver
```

API em `http://localhost:8000/api/`.
Admin em `http://localhost:8000/admin/`.
Swagger UI em `http://localhost:8000/api/docs/`.

## Comandos úteis

```bash
# Lint + format
ruff check .
ruff format .

# Testes
pytest
pytest --cov                  # com coverage

# Shell Django
python manage.py shell

# Nova migration
python manage.py makemigrations <app> --name descritivo

# Aplicar migrations
python manage.py migrate
```

## Celery (a partir do Bloco 2)

```bash
# Em outro terminal
celery -A arminda worker --loglevel=info

# Beat (jobs agendados)
celery -A arminda beat --loglevel=info
```
