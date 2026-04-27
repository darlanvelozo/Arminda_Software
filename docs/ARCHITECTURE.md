# Arquitetura

> Visão técnica de alto nível do Arminda. Decisões pontuais com racional próprio estão registradas em [adr/](adr).

---

## Visão geral

O Arminda é um SaaS multi-tenant. Cada município é um tenant isolado, com seus próprios dados de servidores, folha, rubricas e histórico. A aplicação é um **monolito modular** (Django + DRF) servindo uma SPA (React).

```
┌─────────────────────────────────────────────────────────────┐
│                      Cliente (browser)                       │
│              Vite + React + TS + Tailwind                    │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTPS / JSON
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend Django                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │  API REST (Django REST Framework)                   │    │
│  │  Autenticação JWT • RBAC • Multi-tenant middleware  │    │
│  └────────────────────────────────────────────────────┘    │
│  ┌──────────┬──────────┬──────────┬──────────┐             │
│  │   core   │  people  │ payroll  │ reports  │  apps       │
│  └──────────┴──────────┴──────────┴──────────┘             │
└──────────┬─────────────────────────┬────────────────────────┘
           │                         │
           ▼                         ▼
   ┌──────────────┐         ┌──────────────┐
   │  PostgreSQL  │         │    Redis     │
   │  (multi-     │         │  (cache +    │
   │   tenant     │         │   broker     │
   │   por        │         │   Celery)    │
   │   schema)    │         │              │
   └──────────────┘         └──────────────┘
                                    │
                                    ▼
                            ┌──────────────┐
                            │   Celery     │
                            │   workers    │
                            │ (cálculo,    │
                            │  eSocial,    │
                            │  relatórios) │
                            └──────────────┘
```

---

## Decisões fundamentais

### Backend: Django + DRF
- Domínio fortemente relacional (folha = grafo de relações).
- Django ORM lida bem com schemas dinâmicos (multi-tenant).
- Admin do Django acelera ferramentas internas e auditoria.
- DRF para a API REST.
- Ver [ADR-0002](adr/0002-django-backend.md).

### Frontend: Vite + React + TS
- Vite tem build/dev rápido e configuração mínima.
- React com TypeScript dá tipagem forte na fronteira API ↔ UI.
- shadcn/ui para componentes acessíveis e copiáveis (sem lock-in de biblioteca).
- TanStack Query para cache de servidor.
- Ver [ADR-0003](adr/0003-vite-react-frontend.md).

### Banco: PostgreSQL multi-tenant por schema
- Um schema por município → isolamento forte, backup/restore por tenant, fácil exclusão.
- Schema `public` guarda metadados compartilhados (configurações legais, layouts TCE, usuários globais).
- Ver [ADR-0004](adr/0004-multi-tenant-schema.md).

### Cálculo assíncrono: Redis + Celery
- Folha de 16k servidores não pode bloquear request HTTP.
- Celery permite filas separadas para tipos de job (folha, eSocial, relatórios, importação).
- Redis também serve como cache e store de sessão.

### Monorepo
- Backend e frontend no mesmo repositório.
- Simplifica versionamento, CI e contexto para desenvolvedor solo.
- Deploys são independentes (cada lado tem seu pipeline).
- Ver [ADR-0001](adr/0001-monorepo.md).

---

## Modelo de domínio (visão inicial)

```
Tenant (Município)
  ├── User (com papéis)
  ├── Servidor (pessoa física)
  │     ├── Documento
  │     ├── Dependente
  │     └── HistóricoFuncional
  ├── Cargo
  ├── Lotação
  ├── VínculoFuncional (servidor × cargo × lotação × regime)
  ├── Rubrica (com fórmula DSL)
  ├── Folha (competência + tipo)
  │     └── Lançamento (servidor × rubrica × folha)
  └── EventoESocial (fila de envio)
```

Detalhamento por entidade virá no Bloco 1.

---

## DSL de rubricas (coração do sistema)

Rubricas (proventos e descontos) são **fórmulas configuráveis**, não código. Exemplo conceitual:

```
# Adicional noturno = 20% do salário base por hora noturna trabalhada
resultado = salario_base / carga_horaria_mensal * horas_noturnas * 0.20

incidencias:
  inss: sim
  irrf: sim
  fgts: sim
```

Requisitos da DSL:
1. **Testável** — cada rubrica tem cenários de teste com entrada e resultado esperado.
2. **Versionada** — mudar uma fórmula preserva o cálculo histórico.
3. **Auditável** — o holerite mostra o passo a passo do cálculo.
4. **Sem código arbitrário** — sandbox seguro, sem `eval`, sem acesso a I/O.

Implementação será definida no Bloco 2.

---

## Segurança

- Autenticação por JWT com refresh.
- RBAC com permissões por tela e ação (não só por endpoint).
- Logs de auditoria em todas as escritas relevantes (quem, quando, o quê, antes, depois).
- LGPD by design: criptografia de campos sensíveis (CPF, conta bancária), retenção configurável, exportação de dados pessoais.
- Multi-tenant com middleware que rejeita requests sem tenant resolvido.
- Rate limiting por usuário e por IP.

---

## Observabilidade (a ser instrumentada gradualmente)

- Logs estruturados (JSON) com correlação por request ID.
- Sentry para erros em produção.
- Métricas Prometheus + Grafana para latência, throughput, filas.
- Dashboards específicos para cálculo de folha (nº de servidores, tempo, divergências).

---

## Estratégia de deploy (alvo)

- **Dev local:** Docker Compose (Postgres + Redis), Django e Vite rodando nativamente.
- **Staging:** Railway ou Fly.io (custo baixo, deploy simples).
- **Produção:** AWS (ECS + RDS + ElastiCache) ou similar, definida quando houver primeiro cliente real.

A escolha de produção fica para o final do Bloco 5 — antes disso, o foco é engenharia, não infra.
