# Setup em máquina nova

> Checklist passo-a-passo para subir o Arminda do zero numa máquina nova
> (Linux/macOS/WSL) e ter ambiente de desenvolvimento funcional em ~20 minutos.
>
> Para o **deploy em produção** (VPS), ver [DEPLOY_PRODUCAO.md](DEPLOY_PRODUCAO.md).
> Para **uso operacional do sistema**, ver [`/guia`](../frontend/src/pages/GuiaPage.tsx) (dentro da app).

---

## 1. Pré-requisitos

| Ferramenta | Versão mínima | Como verificar |
|---|---|---|
| Python | 3.12 | `python3 --version` |
| Node.js | 20 | `node --version` |
| npm | 10 | `npm --version` |
| PostgreSQL | 16 | `psql --version` |
| Git | qualquer recente | `git --version` |
| Docker (opcional) | 24 | `docker --version` |

No Ubuntu/Debian:
```bash
sudo apt update
sudo apt install -y python3.12 python3.12-venv python3-pip nodejs npm postgresql-16 postgresql-contrib git
```

No macOS (Homebrew):
```bash
brew install python@3.12 node postgresql@16 git
```

---

## 2. Clonar o repositório

```bash
git clone https://github.com/darlanvelozo/Arminda_Software.git
cd Arminda_Software
```

Se você usa Claude Code, o arquivo [`CLAUDE.md`](../CLAUDE.md) na raiz será
lido automaticamente e ele já vai saber as regras de processo do projeto.

---

## 3. Variáveis de ambiente

```bash
cp .env.example .env
```

O `.env.example` tem defaults seguros para dev local. Você só precisa
mexer se for usar credenciais diferentes do `arminda:arminda_dev_password`
no Postgres local.

**Nunca commite o `.env` real.** Já está no `.gitignore`.

---

## 4. PostgreSQL local

### Opção A — Docker Compose (mais rápido)

```bash
docker compose up -d
```

Sobe Postgres na porta 5432 e Redis na 6379. Variáveis já casam com `.env.example`.

### Opção B — Postgres nativo

```bash
sudo -u postgres psql <<EOF
CREATE USER arminda WITH PASSWORD 'arminda_dev_password';
CREATE DATABASE arminda OWNER arminda;
ALTER USER arminda CREATEDB;  -- necessário para django-tenants criar schemas
EOF
```

Redis precisa estar rodando se você for testar features que usam Celery
(em dev, a maioria não usa).

---

## 5. Backend (Django + DRF)

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate          # Linux/Mac
# .venv\Scripts\activate            # Windows

pip install --upgrade pip
pip install -r requirements.txt
```

### 5.1 Migrations e tenant inicial

O Arminda é multi-tenant. Cada município é um schema PostgreSQL. A
primeira migration cria o `public` (compartilhado) com `Municipio`,
`Usuario` e papéis (estes vêm seedados via migration `0002_seed_grupos_papeis`).

```bash
# settings dev (alias) — exporte uma vez por sessão
export DJANGO_SETTINGS_MODULE=arminda.settings.dev

# Cria public + roda migrations no SHARED (inclui seed dos 5 grupos RBAC:
# staff_arminda, admin_municipio, rh_municipio, financeiro_municipio, leitura_municipio)
python manage.py migrate_schemas --shared

# Cria um superuser pra acessar /admin
python manage.py createsuperuser
```

### 5.2 Criar o primeiro tenant (município)

```bash
python manage.py criar_municipio \
  --schema mun_smoke \
  --nome "Município de Smoke" \
  --uf MA \
  --codigo-ibge 2111300
# opcional em dev: --dominio smoke.localhost
```

Esse comando cria o schema `mun_smoke` e roda migrations dentro dele.
A partir de agora, requests com header `X-Tenant: mun_smoke` operam
neste município.

Pra listar tenants existentes:

```bash
python manage.py listar_tenants
```

### 5.3 Criar usuário do tenant e atribuir papel

```bash
python manage.py criar_usuario \
  --email smoke-admin@arminda.local \
  --senha "trocar-em-prod" \
  --nome "Admin Smoke" \
  --municipio-schema mun_smoke \
  --papel admin_municipio
```

Papéis disponíveis: `staff_arminda`, `admin_municipio`, `rh_municipio`,
`financeiro_municipio`, `leitura_municipio`.

### 5.4 Subir o servidor de dev

```bash
python manage.py runserver
```

API em http://localhost:8000. Admin em http://localhost:8000/admin.
Swagger em http://localhost:8000/api/docs/.

### 5.5 (opcional) Importar base do Fiorilli SIP

Se você tiver o arquivo `SIP.FDB` (Firebird) do município que quer
importar, pode usar o pipeline ETL da Onda 1.4:

```bash
# Subir Firebird 2.5 com o FDB
docker run -d --name fb25 -p 13050:3050 \
  -v /caminho/para/SIP.FDB:/firebird/data/SIP.FDB \
  -e ISC_PASSWORD=masterkey \
  jacobalberty/firebird:2.5-ss

# Rodar importador
python manage.py import_fiorilli_sip \
  --tenant mun_smoke \
  --host 127.0.0.1 --port 13050 \
  --database /firebird/data/SIP.FDB \
  --user SYSDBA --password masterkey \
  --tabelas cargos,lotacoes,servidores,dependentes,vinculos,unidades_orcamentarias
```

Detalhes em [adr/0009-importador-fiorilli-sip.md](adr/0009-importador-fiorilli-sip.md).

---

## 6. Frontend (React + Vite)

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

Interface em http://localhost:5173. Login com o usuário criado em 5.3.

### 6.1 (opcional) Regenerar tipos TypeScript a partir do OpenAPI

Útil quando você muda serializers no backend:

```bash
# Com backend rodando em :8000
npm run gen:types

# Ou offline (snapshot do schema)
npm run gen:types:offline
```

---

## 7. Smoke test rápido

```bash
# Backend smoke
curl -s http://localhost:8000/api/health/ | python3 -m json.tool

# Frontend smoke
curl -s http://localhost:5173/ | grep -c "Arminda"

# Backend tests
cd backend && source .venv/bin/activate
DJANGO_SETTINGS_MODULE=arminda.settings.dev python -m pytest -q

# Frontend tests
cd frontend
npm run lint
npx tsc --noEmit
npx vitest run
```

Esperado:
- `/api/health/` retorna `{"status":"ok","service":"arminda"}`
- 441+ testes backend passando
- 10+ testes frontend passando
- Sem erros de lint nem typecheck

---

## 8. SSH config para a VPS de produção (opcional)

Se for fazer deploy, configure o alias `arminda-vps` em `~/.ssh/config`:

```ssh-config
Host arminda-vps
  HostName 2.24.122.160
  User root
  IdentityFile ~/.ssh/id_ed25519
```

Sua chave SSH precisa estar autorizada no painel da Hostinger ou via
`ssh-copy-id`. Depois, comandos como `ssh arminda-vps` funcionam direto.

Operação de produção: [DEPLOY_PRODUCAO.md](DEPLOY_PRODUCAO.md).

---

## 9. Próximos passos

1. Ler [CLAUDE.md](../CLAUDE.md) se for usar Claude Code (instruções de processo)
2. Ler [CONTEXT.md](../CONTEXT.md) (raiz) — contexto global
3. Ler [docs/ROADMAP.md](ROADMAP.md) — onde estamos e o que vem
4. Ler [docs/PERSONAS.md](PERSONAS.md) — quem usa o sistema
5. Ler `CONTEXT.md` do escopo onde for trabalhar (backend, frontend, etc.)
6. Começar a próxima onda ou pegar um bug pendente

---

## 10. Solução de problemas comuns

### `psycopg.OperationalError: FATAL: role "arminda" does not exist`
Você não rodou o passo 4. Crie o usuário Postgres conforme 4.B ou use Docker (4.A).

### `relation "django_tenants_..." does not exist`
Faltou `migrate_schemas --shared`. Rode novamente o passo 5.1.

### Login retorna 400 `TENANT_NAO_RESOLVIDO`
Você não passou header `X-Tenant`. No frontend, isso é automático após o
"selecionar município". Em chamadas manuais, inclua `-H "X-Tenant: mun_smoke"`.

### Frontend não carrega tipos
Backend precisa estar rodando para `npm run gen:types`. Ou use `npm run gen:types:offline`.

### Migrations em tenants existentes não atualizam
Quando você adiciona migration nova em `apps/people` (TENANT_APP), rode:
```bash
python manage.py migrate_schemas
```
Isso aplica em TODOS os tenants. Sem `--shared`, ele cuida do que está em `TENANT_APPS`.

### Testes muito lentos (primeira execução)
A primeira execução cria 2 tenants de teste (`test_tenant_a`, `test_tenant_b`)
e roda migrations em cada um. ~30s overhead. Execuções seguintes são rápidas.

### "openpyxl not found" ao testar importador CSV
```bash
pip install openpyxl==3.1.5
```
Já está em `requirements.txt`, mas pode ter ficado para trás se você
clonou em paralelo a uma onda 1.6b em desenvolvimento.
