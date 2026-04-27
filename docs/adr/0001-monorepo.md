# ADR-0001 — Monorepo (backend + frontend no mesmo repositório)

**Status:** Aceito
**Data:** 2026-04-27

## Contexto

O Arminda tem dois deliverables principais: uma API Django e uma SPA React. A primeira decisão estrutural é se eles vivem no mesmo repositório ou em repositórios separados.

O projeto começa com um único desenvolvedor (Darlan, 20h/semana), com possibilidade de crescer para uma equipe pequena nos próximos meses. Não há restrições organizacionais (políticas de equipe, segurança ou compliance) que forcem separação.

## Decisão

Adotar **monorepo** com pastas `backend/` e `frontend/` no mesmo repositório (`Arminda_Software`).

## Consequências

**Positivas**
- Um único `git clone` traz o projeto completo.
- Mudanças que cruzam as duas pontas (mudar contrato de API e ajustar consumo) ficam em um único PR, facilitando revisão e rollback.
- Documentação central (README, ROADMAP, ADRs) serve para tudo.
- CI configurado uma vez, com jobs separados por subpasta.
- Versionamento e tags são unificados.

**Negativas / mitigações**
- O `node_modules` cresce dentro de `frontend/`. Mitigação: `.gitignore` cuida disso.
- Times grandes podem ter conflitos de merge mais frequentes. Mitigação: enquanto for solo/duo, isso não importa; se o time crescer muito, pode-se migrar para polyrepo depois.
- Pipelines de CI precisam saber qual lado mudou para evitar builds desnecessários. Mitigação: usar `paths:` filter no GitHub Actions.

## Alternativas consideradas

- **Polyrepo (dois repositórios separados)** — descartado. Em time pequeno, dobra a fricção (dois clones, dois CIs, dois fluxos de release) sem trazer benefício real.
- **Monorepo com Nx/Turborepo** — descartado por enquanto. Overkill para dois projetos simples; pode ser adotado depois se o sistema crescer (ex.: separar packages compartilhados).
