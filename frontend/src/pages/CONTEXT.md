# frontend/src/pages/CONTEXT.md — Regras de Páginas

> Regras para componentes de página (componentes mapeados em rotas).
> **Antes de criar/alterar uma página, ler este arquivo + [`frontend/CONTEXT.md`](../../CONTEXT.md).**

---

## 1. O que é uma página

Página = componente React montado em uma **rota** do React Router. Responsabilidades:

1. Buscar dados que ela precisa (via hooks de API).
2. Compor componentes de domínio + UI primitives.
3. Tratar estados de **loading**, **erro**, **vazio** e **sucesso**.
4. Lidar com parâmetros de URL e navegação.

**O que página NÃO faz:**
- ❌ Lógica de negócio (não tem; backend faz).
- ❌ Chamadas HTTP cruas (vai por hook).
- ❌ Estilização rebuscada inline (compor componentes).
- ❌ Estado global de UI (use Context/zustand quando precisar).

---

## 2. Estrutura de pasta

```
src/pages/
├── CONTEXT.md
├── HomePage.tsx                ← landing
├── HealthPage.tsx              ← /status, /health
├── NotFoundPage.tsx            ← 404
├── auth/                       ← (Bloco 1)
│   ├── LoginPage.tsx
│   └── EsqueciSenhaPage.tsx
├── people/                     ← (Bloco 1)
│   ├── ServidorListPage.tsx
│   ├── ServidorDetailPage.tsx
│   ├── ServidorEditPage.tsx
│   └── AdmissaoPage.tsx
└── payroll/                    ← (Bloco 2)
    ├── FolhaListPage.tsx
    └── FolhaDetailPage.tsx
```

### Quando agrupar em subpasta
- Mais de **2 páginas** da mesma área → subpasta (`auth/`, `people/`, `payroll/`).
- Páginas avulsas e únicas → ficam em `src/pages/` direto.

---

## 3. Convenção de naming

- **Sufixo `Page`** sempre: `ServidorListPage`, `LoginPage`, `NotFoundPage`.
- Naming reflete **rota + ação** quando aplicável:
  - `ServidorListPage` → `/people/servidores`
  - `ServidorDetailPage` → `/people/servidores/:id`
  - `ServidorEditPage` → `/people/servidores/:id/editar`
  - `AdmissaoPage` → `/people/servidores/admitir`

---

## 4. Esqueleto de página

```tsx
import { useParams, useNavigate } from "react-router-dom";
import { useServidor } from "@/hooks/useServidor";
import { ServidorHeader } from "@/components/people/ServidorHeader";
import { VinculoList } from "@/components/people/VinculoList";
import { LoadingState } from "@/components/feedback/LoadingState";
import { ErrorState } from "@/components/feedback/ErrorState";

export default function ServidorDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data, isLoading, isError, error } = useServidor(Number(id));

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} onRetry={() => navigate(0)} />;
  if (!data) return null;

  return (
    <main className="container py-8 space-y-6">
      <ServidorHeader servidor={data} />
      <VinculoList vinculos={data.vinculos} />
    </main>
  );
}
```

### Regras
- **`export default`** — facilita lazy loading e padronização de import na config de rotas.
- **Hooks no topo, em ordem fixa** (regras do React).
- **Quatro estados sempre tratados:** loading, error, empty, success.
- **Não compor páginas dentro de páginas.** Composição vai em componentes.

---

## 5. Tratamento de estados

### Loading
- Componente `<LoadingState />` (a criar em `src/components/feedback/`).
- Skeleton quando o conteúdo tiver shape previsível (lista, formulário); spinner quando não tiver.

### Erro
- Componente `<ErrorState error onRetry />`.
- Mensagem amigável em português; **não vazar stacktrace** para o usuário.
- Botão de **tentar novamente**.
- Erros 401 redirecionam para `/login` (interceptor axios — Bloco 1).

### Vazio
- Mensagem clara + CTA para o caso aplicável: `"Nenhum servidor cadastrado. [Cadastrar primeiro]"`.

### Sucesso
- Render normal.

---

## 6. Parâmetros de URL e query string

```tsx
import { useParams, useSearchParams } from "react-router-dom";

const { id } = useParams<{ id: string }>();
const [searchParams, setSearchParams] = useSearchParams();
const page = Number(searchParams.get("page") ?? 1);
const search = searchParams.get("q") ?? "";
```

- **Sempre validar** que params existem antes de usar (`Number(id)` pode dar `NaN`).
- **Filtros e paginação** devem ir para query string — permite link compartilhável.
- **Estado controlado pela URL** (filtros, ordenação, página) > estado local. URL é a única fonte da verdade.

---

## 7. Formulários

- Pequenos (≤ 5 campos): `useState` controlado.
- Médios/grandes: `react-hook-form + zod` (a partir do Bloco 1).
- **Validação:**
  - Cliente (UX, feedback imediato): zod schema.
  - Servidor (autoritativo): se backend retorna 400, mapear `error.code` para mensagem amigável.
- Botão de submit em loading durante mutation; **desabilitar** para evitar duplo envio.
- Após sucesso: **toast** + navegação ou invalidação de query.

---

## 8. Navegação

```tsx
import { Link, useNavigate } from "react-router-dom";

// Link declarativo (preferir)
<Link to={`/people/servidores/${servidor.id}`}>Ver detalhe</Link>

// Imperativo (após mutation, redirect)
const navigate = useNavigate();
navigate(`/people/servidores/${novoServidor.id}`);
```

- **Nunca** `window.location.href = "..."` para navegação interna.
- **Externos** (`https://...`): `<a target="_blank" rel="noopener noreferrer">`.

---

## 9. Acessibilidade da página

- **`<main>`** envolve o conteúdo principal (já adotado em `HomePage.tsx`).
- **Hierarquia de heading correta:** um `<h1>` por página, seguir `<h2>`, `<h3>`.
- **Foco** visível em links, botões, inputs (Tailwind: `focus-visible:`).
- **Mudança de rota:** focar no `<h1>` após navegar (boa prática para leitor de tela — implementar helper no Bloco 1).

---

## 10. Code-splitting

A partir do Bloco 1, páginas pesadas via `React.lazy`:

```tsx
import { lazy, Suspense } from "react";

const RelatoriosPage = lazy(() => import("@/pages/reports/RelatoriosPage"));

<Route
  path="/relatorios"
  element={
    <Suspense fallback={<LoadingState />}>
      <RelatoriosPage />
    </Suspense>
  }
/>
```

- Aplicar em páginas com bundle > 100KB ou rotas de uso esporádico.
- **Não** aplicar em landing/login (impacto negativo no first-paint).

---

## 11. Testes de página

- Foco: **smoke + interação principal**, não cada detalhe.
- Mock de hooks de API via `vi.mock("@/hooks/...")` ou `QueryClientProvider` com data prefetch.
- Exemplo:

```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import HomePage from "@/pages/HomePage";

function renderWithProviders(ui: React.ReactNode) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>
  );
}

describe("HomePage", () => {
  it("mostra o título do produto", () => {
    renderWithProviders(<HomePage />);
    expect(screen.getByRole("heading", { name: /arminda/i })).toBeInTheDocument();
  });
});
```

(`src/test/HomePage.test.tsx` já é o esqueleto — manter o helper `renderWithProviders` em `src/test/utils.tsx` quando crescer.)

---

## 12. Páginas existentes

| Página | Rota | Observação |
|--------|------|------------|
| `HomePage` | `/` | Landing temporária (Bloco 0) |
| `HealthPage` | `/health` e `/status` | Consome `/health/` e `/status/` do backend |
| `NotFoundPage` | `*` | 404 |

A partir do Bloco 1: `HomePage` provavelmente será dashboard autenticado, com landing pública separada.

---

## 13. Checklist antes de commitar uma página

- [ ] Hook de API por dado buscado, via TanStack Query.
- [ ] 4 estados (loading/error/empty/success) tratados.
- [ ] Tipos completos, sem `any`.
- [ ] Texto em português, código em inglês.
- [ ] `<main>` + heading hierárquico correto.
- [ ] Filtros/paginação na URL (não em estado local).
- [ ] Teste de smoke da página.
- [ ] Lighthouse a11y ≥ 90 quando rodável.
- [ ] Entrada no `CHANGELOG.md`.
