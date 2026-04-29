# frontend/CONTEXT.md — Regras do Frontend

> Contexto e regras de implementação do frontend React.
> **Antes de qualquer alteração, consulte também o [`CONTEXT.md`](../CONTEXT.md) raiz.**

---

## 1. Stack e versões fixadas

- **Vite 6**
- **React 18.3 + React DOM 18.3**
- **TypeScript 5.7** (strict)
- **TailwindCSS 3.4** + tokens CSS shadcn-ready (em `src/styles/globals.css`)
- **shadcn/ui** (componentes copiáveis via CLI; sem dependência runtime do shadcn)
- **TanStack Query 5** — estado de servidor / cache
- **React Router 7** — rotas
- **axios 1.7** — HTTP
- **zod 3** — validação de schemas (formulários, runtime)
- **lucide-react** — ícones
- **class-variance-authority + clsx + tailwind-merge** — composição de classes (helper `cn` em `src/lib/utils.ts`)
- **vitest 2 + @testing-library/react** — testes
- **eslint 9 (flat config) + prettier 3** — qualidade

Mudança de versão: PR específico de upgrade, com nota em `CHANGELOG.md`.

---

## 2. Estrutura de pastas

```
frontend/
├── public/                       ← assets estáticos
├── src/
│   ├── components/
│   │   ├── CONTEXT.md            ← regras de componentes
│   │   ├── ui/                   ← componentes shadcn (Button, Input, etc.)
│   │   ├── layout/               ← AppShell, Sidebar, Header (Bloco 1+)
│   │   └── <Dominio>/            ← componentes de domínio (ServidorList, FolhaCard)
│   ├── pages/
│   │   ├── CONTEXT.md            ← regras de páginas
│   │   ├── HomePage.tsx
│   │   ├── HealthPage.tsx
│   │   ├── NotFoundPage.tsx
│   │   └── <area>/               ← agrupamento por área de negócio (people, payroll)
│   ├── lib/
│   │   ├── api.ts                ← instância axios
│   │   ├── utils.ts              ← cn() e helpers transversais
│   │   ├── auth.ts               ← (Bloco 1) auth helpers + interceptor JWT
│   │   └── format.ts             ← (Bloco 1) format moeda BR, CPF, datas
│   ├── hooks/                    ← (Bloco 1+) hooks customizados
│   │   └── use<Algo>.ts
│   ├── features/                 ← (opcional, Bloco 2+) lógica por feature
│   │   └── <feature>/
│   │       ├── api.ts
│   │       ├── hooks.ts
│   │       └── types.ts
│   ├── routes/                   ← (Bloco 1) config de rotas + guards
│   ├── styles/
│   │   └── globals.css           ← tokens CSS + Tailwind
│   ├── test/                     ← setup e testes globais
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── package.json
├── tsconfig.json / tsconfig.app.json / tsconfig.node.json
├── tailwind.config.ts
├── vite.config.ts
└── vitest.config.ts
```

**Estado atual (Bloco 0):** apenas `src/lib/`, `src/pages/`, `src/styles/`, `src/test/`.
A pasta `src/components/` será criada quando entrar a primeira tela do Bloco 1 (ver `src/components/CONTEXT.md`).

---

## 3. Convenções obrigatórias

### Idioma
- **Texto de UI, mensagens, labels:** português (clientes brasileiros).
- **Código (variáveis, funções, componentes, types):** inglês.
- **Exceção:** termos de domínio brasileiro intraduzíveis (`Servidor`, `Lotacao`, `Folha`, `Holerite`) podem aparecer em nomes quando refletem o tipo do backend (`type Servidor = ...` para casar com a API).

### Naming
- **Componentes:** PascalCase. `ServidorList`, `FolhaCard`, `HoleriteViewer`.
- **Hooks:** camelCase prefixado com `use`. `useServidores`, `useFolhaAtual`.
- **Funções utilitárias:** camelCase. `formatCpf`, `formatCurrency`.
- **Tipos/interfaces:** PascalCase. `Servidor`, `FolhaResumo`. Preferir `interface` para shape de objeto, `type` para união/utilitário.
- **Arquivos de componente:** mesmo nome do componente (`ServidorList.tsx`).
- **Arquivos de hook:** kebab-case ou camelCase consistente — adotar **camelCase** (`useServidores.ts`).

### TypeScript
- **`strict: true`** (já configurado).
- **`any` proibido em código novo.** Usar `unknown` e narrow.
- **Sem `// @ts-ignore`** para ignorar erro real — corrigir o tipo.
- Interfaces para **shape externo** (resposta de API). Types para **derivações/uniões**.
- `zod` quando precisar de **validação em runtime** (formulários, dados externos não confiáveis).

### Imports
- Usar alias `@/` (mapeado para `src/`):
  ```ts
  import { api } from "@/lib/api";
  import HomePage from "@/pages/HomePage";
  ```
- **Proibido** `../../../`. Se aparece, ou usa `@/`, ou é sinal de pasta no lugar errado.
- Ordem (prettier+eslint): externos → `@/...` → relativos `./...`.

### Lint/format
```bash
cd frontend
npm run format         # prettier escreve
npm run lint           # eslint
npm run format:check   # CI
```
PR não passa sem ambos verdes.

---

## 4. Padrão de chamada à API

### Cliente único: `src/lib/api.ts`
Instância axios configurada. **Não criar outra.**

### Buscas → TanStack Query (`useQuery`)

```ts
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

interface Servidor {
  id: number;
  matricula: string;
  nome: string;
  cpf: string;
  ativo: boolean;
}

interface ListResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export function useServidores(params: { page?: number; search?: string } = {}) {
  return useQuery({
    queryKey: ["servidores", params],
    queryFn: async () => {
      const { data } = await api.get<ListResponse<Servidor>>("/people/servidores/", { params });
      return data;
    },
  });
}
```

### Mutações → `useMutation`

```ts
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function useAdmitirServidor() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (dados: AdmissaoInput) => {
      const { data } = await api.post<Servidor>("/people/servidores/admitir/", dados);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["servidores"] });
    },
  });
}
```

### Regras
- **Toda chamada de API passa por `useQuery`/`useMutation`** — sem `useEffect + axios` solto.
- **`queryKey` consistente:** `[recurso, params]`. Permite invalidação cirúrgica.
- **Hooks de API ficam em `src/features/<area>/api.ts` ou `src/hooks/`** (a definir quando crescer; no Bloco 1 começamos em `src/hooks/`).
- **Tipos vêm do schema OpenAPI** — investigar geração automática (`openapi-typescript`) no Bloco 1; até lá, manter manualmente em sincronia.

---

## 5. Roteamento (React Router 7)

- Rotas centralizadas em `src/App.tsx` no Bloco 0 → migrar para `src/routes/index.tsx` no Bloco 1 quando crescer.
- **Code-splitting** por `lazy(() => import(...))` em páginas pesadas (relatórios, BI).
- **Guards de auth** via componente wrapper `<RequireAuth>` (Bloco 1).
- **404** sempre tratado (`<Route path="*" element={<NotFoundPage />} />`).

---

## 6. Estilo (Tailwind + shadcn/ui)

### Filosofia
- **Tailwind para tudo que é layout, espaçamento, cor, tipografia.**
- **shadcn/ui** para primitivos acessíveis (Button, Input, Dialog, DropdownMenu).
- **Sem CSS-in-JS** (styled-components, emotion). Sem CSS modules. Apenas:
  - `globals.css` para tokens e overrides globais.
  - Classes Tailwind direto no JSX.

### Helper `cn`
Para condicionais e merge de classes Tailwind:
```ts
import { cn } from "@/lib/utils";

<button className={cn(
  "rounded-md px-4 py-2 font-medium transition",
  variant === "primary" && "bg-primary text-primary-foreground",
  variant === "ghost" && "bg-transparent hover:bg-accent",
  disabled && "opacity-50 cursor-not-allowed",
)}>
```

### Cores
- Usar **tokens CSS** (`bg-primary`, `text-muted-foreground`, etc.), não hex literais.
- Tokens definidos em `src/styles/globals.css` (já configurado para shadcn).
- **Suporte a dark mode** via classe `dark` no `<html>` (a habilitar no Bloco 1).

### Adicionar componente shadcn
```bash
npx shadcn@latest add button
npx shadcn@latest add input
```
- Vai para `src/components/ui/<Component>.tsx`.
- **Versionado no repo** (sem dependência de runtime do shadcn).
- **Customizar livremente** depois de copiado.

---

## 7. Estado

- **Estado de servidor:** TanStack Query. Cache, invalidação, retry, refetch — tudo dele.
- **Estado de UI local:** `useState`/`useReducer`.
- **Estado global de UI** (sidebar aberta, tema): `Context` simples ou `zustand` se crescer (decisão posposta para Bloco 1+).
- **Estado de formulário:** começar com `useState` controlado; trocar para `react-hook-form + zod` quando o formulário tiver > 5 campos ou validação complexa (Bloco 1).

---

## 8. Acessibilidade

- Todo botão é `<button>` (não `<div onClick>`).
- Todo input tem `<label>` associado (`htmlFor` + `id`).
- Diálogos/menus usam primitivos shadcn (já trazem ARIA correto).
- Cores com **contraste mínimo AA** (4.5:1 texto normal).
- **Lighthouse a11y ≥ 90** é gate do Bloco 7 (e bom hábito antes).

---

## 9. Testes

### Estrutura
- Setup global em `src/test/setup.ts` (já configurado: `@testing-library/jest-dom`).
- Co-localizar teste com componente: `Button.tsx` + `Button.test.tsx`. Página em `src/pages/HomePage.tsx` + `src/test/HomePage.test.tsx` (atual).
- Decisão de organização: **co-localização** (`src/components/Foo.tsx` + `Foo.test.tsx`) será adotada a partir do Bloco 1.

### Padrão
```tsx
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { Button } from "@/components/ui/Button";

describe("Button", () => {
  it("renderiza o label", () => {
    render(<Button>Salvar</Button>);
    expect(screen.getByRole("button", { name: "Salvar" })).toBeInTheDocument();
  });

  it("dispara onClick", async () => {
    const onClick = vi.fn();
    render(<Button onClick={onClick}>OK</Button>);
    await userEvent.click(screen.getByRole("button"));
    expect(onClick).toHaveBeenCalledOnce();
  });
});
```

### Regras
- **Testar comportamento, não implementação** — usar `getByRole`, `getByLabelText`, evitar `getByTestId` salvo necessidade.
- **Mock só na fronteira** (módulo `@/lib/api`). Não mockar componentes filhos.
- **Hooks de API testados via `QueryClientProvider` wrapper** (helper a criar em `src/test/utils.tsx`).
- **Cobertura mínima:** componentes de domínio críticos, hooks de API, validações zod. Não perseguir 100% em layout puro.

### Comandos
```bash
npm test                  # vitest watch
npm run test:coverage     # com cobertura
```

---

## 10. Variáveis de ambiente

- Apenas variáveis prefixadas `VITE_` ficam disponíveis no client.
- `VITE_API_URL` — URL base da API (default em dev: `http://localhost:8000/api`).
- `VITE_APP_NAME` — branding.
- **Nunca** variável sensível no client (chaves de API, secrets). Vite expõe tudo `VITE_*` no bundle.

---

## 11. O que NUNCA fazer no frontend

- ❌ Chamar `fetch`/`axios` direto em componente (sempre via hook + TanStack Query).
- ❌ `any` em código novo.
- ❌ `// @ts-ignore` ou `// eslint-disable` sem justificativa em comentário.
- ❌ Imports relativos profundos (`../../../`).
- ❌ Hex de cor hardcoded em JSX (use tokens CSS via Tailwind).
- ❌ CSS-in-JS, CSS modules, styled-components.
- ❌ Editar componente shadcn sem registrar a customização (manter histórico claro).
- ❌ Lógica de negócio no frontend (cálculo de folha não é responsabilidade do client; o backend devolve pronto).
- ❌ `console.log` deixado em commit (vira ruído + lint warning).
- ❌ Usar `window.location.href = ...` para navegação interna (use React Router).

---

## 12. O que SEMPRE fazer no frontend

- ✅ Ler este arquivo + o `CONTEXT.md` específico (components/pages) antes de codar.
- ✅ Atualizar `CHANGELOG.md` ao final.
- ✅ Atualizar este arquivo se o padrão mudar.
- ✅ Tipar tudo (sem `any`).
- ✅ Hook por chamada de API; TanStack Query.
- ✅ shadcn primitives + Tailwind.
- ✅ Tradução PT-BR em toda string visível ao usuário.
- ✅ `npm run lint && npm run format:check && npm test` antes de commitar.

---

## 13. Comandos de referência

```bash
npm install
npm run dev               # dev server (http://localhost:5173)
npm run build             # build de produção
npm run preview           # preview do build
npm run lint              # eslint
npm run format            # prettier escreve
npm run format:check      # prettier verifica
npm test                  # vitest watch
npm run test:coverage     # cobertura

npx shadcn@latest add <componente>   # adicionar primitive shadcn
```
