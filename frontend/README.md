# Frontend — Arminda

SPA do Arminda em Vite + React + TypeScript + Tailwind.

## Estrutura

```
frontend/
├── public/                # assets estáticos
├── src/
│   ├── components/
│   │   └── ui/            # componentes shadcn/ui (vão sendo adicionados)
│   ├── lib/
│   │   ├── api.ts         # cliente axios
│   │   └── utils.ts       # helper cn()
│   ├── pages/             # páginas (rotas)
│   ├── routes/            # config de rotas avançada (Bloco 1+)
│   ├── styles/
│   │   └── globals.css    # tokens CSS + Tailwind
│   ├── test/              # setup e testes globais
│   ├── App.tsx
│   └── main.tsx
├── index.html
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── vite.config.ts
```

## Setup

```bash
npm install
npm run dev
```

App em `http://localhost:5173`. Em dev, requests para `/api/*` são proxiadas para `http://localhost:8000` (Django).

## Comandos

```bash
npm run dev               # dev server
npm run build             # build de produção
npm run preview           # preview do build
npm run lint              # eslint
npm run format            # prettier escreve
npm run format:check      # prettier verifica
npm test                  # vitest watch
npm run test:coverage     # com coverage
```

## Adicionando componentes shadcn/ui

A partir do Bloco 1, usaremos a CLI do shadcn para copiar componentes:

```bash
npx shadcn@latest add button
npx shadcn@latest add input
# etc.
```

Os componentes vão para `src/components/ui/` e ficam versionados no repo (sem lock-in).

## Variáveis de ambiente

Apenas variáveis prefixadas com `VITE_` ficam disponíveis no client. Veja `.env.example` na raiz do repo.
