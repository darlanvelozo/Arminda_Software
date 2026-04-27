# ADR-0003 — Frontend em Vite + React + TypeScript

**Status:** Aceito
**Data:** 2026-04-27

## Contexto

O frontend do Arminda precisa entregar:
- SPA com várias telas (cadastros, folha, relatórios, dashboards)
- UX moderna e responsiva (web e mobile via PWA)
- Tipagem forte na fronteira API ↔ UI
- Build rápido para o ciclo de desenvolvimento solo
- Curva de aprendizado baixa para desenvolvedores juniores futuros

Alternativas avaliadas: Vite + React, Next.js, Vue + Vite, SvelteKit.

## Decisão

Adotar **Vite 5 + React 18 + TypeScript** como base do frontend, com:
- **TailwindCSS** para estilização utility-first
- **shadcn/ui** para componentes acessíveis copiáveis
- **TanStack Query** para cache de servidor
- **React Router** para roteamento client-side
- **Zod** para validação de schemas

## Consequências

**Positivas**
- Vite tem dev server e build extremamente rápidos.
- Stack simples e direta — SPA pura, sem complexidade de SSR.
- Fácil de hospedar (qualquer CDN ou bucket estático).
- shadcn/ui dá componentes profissionais sem lock-in (código vai para o repo).
- React tem o maior ecossistema e a base de talentos mais ampla no Brasil.

**Negativas / mitigações**
- Sem SSR: SEO em landing pages institucionais não é nativo. Mitigação: SaaS B2G — landing pública é mínima; pode-se gerar páginas estáticas separadas se necessário.
- SPA tem first paint mais lento que SSR. Mitigação: code splitting agressivo + skeleton screens.
- Roteamento manual (React Router) versus convenção de pastas do Next. Mitigação: organização clara em `src/routes/` resolve.

## Alternativas consideradas

- **Next.js 15 (App Router)** — mais "estado da arte" hoje, traz SSR/SSG e Server Components. Foi a primeira recomendação. Descartado nesta etapa por preferência do desenvolvedor por simplicidade — Next.js adiciona conceitos (RSC, server actions, Vercel) que aumentam a curva. Pode ser revisitado se SEO ou performance de first paint virarem requisitos críticos.
- **Vue + Vite** — bom DX, mas ecossistema React é maior no contexto do projeto.
- **SvelteKit** — produtividade alta, mas comunidade menor — risco para um produto que precisa durar 5+ anos.

## Stack frontend complementar (escopo deste ADR)

- **Node.js 20+**
- **Vite 5**
- **React 18 + TypeScript 5**
- **Tailwind CSS 3**
- **shadcn/ui** (componentes copiáveis)
- **TanStack Query 5** (estado de servidor)
- **React Router 6** (roteamento)
- **Zod** (validação)
- **Axios** (cliente HTTP)
- **Vitest + Testing Library** (testes)
- **ESLint + Prettier** (lint + format)
