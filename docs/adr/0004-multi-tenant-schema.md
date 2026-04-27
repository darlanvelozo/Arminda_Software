# ADR-0004 — Multi-tenant com isolamento por schema PostgreSQL

**Status:** Aceito
**Data:** 2026-04-27

## Contexto

O Arminda atende múltiplos municípios. Cada município tem seus próprios servidores, folha, rubricas, histórico. Os dados de um município **não podem** vazar para outro — questão de LGPD, de confiança e de conformidade com sigilo funcional.

Existem três padrões usuais para SaaS multi-tenant:

1. **Database por tenant** — cada município tem seu próprio banco PostgreSQL.
2. **Schema por tenant** — um banco PostgreSQL com vários schemas, um por município.
3. **Linha por tenant (shared schema)** — todas as linhas têm uma coluna `tenant_id`, isolamento por filtro.

## Decisão

Adotar **schema por tenant** no PostgreSQL.

Implementação base: biblioteca **django-tenants** (consolidada na comunidade Django, mantida ativamente).

- Schema `public` guarda metadados compartilhados (configurações legais nacionais, layouts TCE, lista de tenants, usuários globais).
- Cada município tem seu schema (ex.: `mun_sao_raimundo`, `mun_teresina`) com todas as tabelas de domínio.
- Middleware resolve o tenant no início do request (via subdomínio ou header) e seta o `search_path` do Postgres para a sessão.

## Consequências

**Positivas**
- **Isolamento forte** — uma query mal escrita não consegue cruzar tenants por engano (search_path filtra).
- **Backup/restore por tenant** é trivial (`pg_dump --schema=mun_xxx`).
- **Exclusão de tenant** é uma operação atômica (`DROP SCHEMA mun_xxx CASCADE`).
- **Performance** — índices ficam menores (apenas dados daquele tenant), planos de query mais eficientes.
- **Migrations por tenant** — ajustes pontuais em um município não exigem touch em todos.
- Conforme com LGPD (princípio de minimização e segregação).

**Negativas / mitigações**
- Migrations precisam rodar em N schemas. Mitigação: `django-tenants` automatiza isso.
- Limite prático de schemas no Postgres é alto (milhares), mas operações de manutenção (vacuum, índices) tem overhead linear. Mitigação: para o horizonte de 100–500 municípios, é confortável; se ultrapassar, podemos sharding por região.
- Backups full do banco crescem com cada tenant. Mitigação: backups por tenant + retenção diferenciada.
- Conexões ao banco precisam setar `search_path`. Mitigação: middleware do `django-tenants` cuida disso.

## Alternativas consideradas

- **Database por tenant** — isolamento ainda mais forte, mas custo operacional explode (N RDS, N pools de conexão, N migrations rodadas separadamente). Faz sentido para clientes enterprise com requisitos jurídicos absurdos; não é o caso de prefeituras.
- **Shared schema (tenant_id em todas as tabelas)** — mais barato em manutenção, mas isolamento depende de lembrar de filtrar em **toda** query. Um único bug de filtragem vaza dados entre municípios. Risco inaceitável num produto que processa folha de pagamento.

## Implicações para o desenvolvimento

- Toda app Django (`apps/people`, `apps/payroll`, etc.) será **tenant app** — suas tabelas vivem nos schemas dos tenants.
- App `core` terá as **tabelas compartilhadas** (Tenant, configurações globais, layouts legais).
- Testes precisam montar pelo menos 2 tenants para garantir que isolamento funciona.
- Importadores de dados (Firebird → Postgres) recebem o tenant como parâmetro obrigatório.

## Referências

- [django-tenants documentation](https://django-tenants.readthedocs.io/)
- [PostgreSQL: Schemas](https://www.postgresql.org/docs/current/ddl-schemas.html)
