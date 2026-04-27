# ADR-0002 — Backend em Django + Django REST Framework

**Status:** Aceito
**Data:** 2026-04-27

## Contexto

O Arminda é um sistema com domínio fortemente relacional (servidor → vínculo → folha → lançamento → rubrica), regras de negócio densas (cálculo, incidências, obrigações legais) e necessidade de telas administrativas internas para auditoria.

As principais alternativas avaliadas foram: Django, FastAPI, Node.js (NestJS) e .NET.

## Decisão

Adotar **Django 5 + Django REST Framework (DRF)** como backend.

## Consequências

**Positivas**
- ORM maduro lida bem com relacionamentos complexos e migrations evolutivas.
- Django Admin acelera ferramentas internas e debug em ambiente real (cliente final não usa, mas operação sim).
- DRF é o padrão de facto para APIs REST em Django, com serializers, viewsets, filtros e permissões prontos.
- Ecossistema rico para o domínio: `django-tenants` (multi-tenant), `django-celery-beat` (jobs agendados), `django-simple-history` (auditoria), bibliotecas para PDF, eSocial, assinatura digital.
- Compatibilidade direta com o desenvolvedor responsável (Darlan tem Python como linguagem principal).

**Negativas / mitigações**
- Django é mais "pesado" que FastAPI em termos de overhead por request. Mitigação: para o volume esperado (centenas a poucos milhares de servidores por município), isso não é gargalo. Quando virar, podemos isolar endpoints críticos em um serviço FastAPI separado.
- Async em Django é mais limitado que em FastAPI. Mitigação: trabalho pesado vai para Celery — endpoints síncronos respondem rápido por design.

## Alternativas consideradas

- **FastAPI** — mais moderno, async-first, mas exige montar mais coisas manualmente (auth, ORM, admin). Bom para microsserviços; menos produtivo para um monolito modular feito por uma pessoa só.
- **NestJS (Node)** — escalável e moderno, mas menos produtivo que Django para CRUD pesado e regras de negócio relacionais. Time menor de devs Node experientes no mercado de "folha de pagamento" no Brasil.
- **.NET** — robusto e usado em alguns sistemas de gestão pública, mas distante do conhecimento do desenvolvedor e custos de licenciamento históricos (Windows Server) atrapalham SaaS enxuto.

## Stack Python complementar (escopo deste ADR)

- **Python 3.12+**
- **Django 5.x**
- **Django REST Framework**
- **psycopg** (driver Postgres v3)
- **Celery + Redis** para tarefas assíncronas
- **pytest + pytest-django** para testes
- **ruff** para lint e formatação
- **pip + requirements.txt** para gestão de dependências (escolha pragmática para a fase inicial)
