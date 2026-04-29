# frontend/src/components/CONTEXT.md — Regras de Componentes

> Regras para componentes reutilizáveis (não-página).
> **Antes de criar/alterar um componente, ler este arquivo + [`frontend/CONTEXT.md`](../../CONTEXT.md).**

---

## 1. Taxonomia: três tipos de componente

```
src/components/
├── ui/                    ← primitivos shadcn (Button, Input, Dialog, ...)
├── layout/                ← estrutura da app (AppShell, Sidebar, Header, Topbar)
└── <Dominio>/             ← componentes ligados ao domínio (people/, payroll/, reports/)
    ├── ServidorCard.tsx
    ├── ServidorList.tsx
    └── ...
```

| Tipo | Onde fica | Tem regra de domínio? | Reusável fora do produto? |
|------|-----------|----------------------|---------------------------|
| **UI primitive** | `ui/` | Não | Sim (poderia virar lib) |
| **Layout** | `layout/` | Não | Específico do produto |
| **Domínio** | `<area>/` | Sim (formato/validação) | Não |

**Regra de ouro:** componente **`ui/`** não importa de **`<dominio>/`**. Componente de domínio importa livremente de `ui/`.

---

## 2. shadcn/ui — `components/ui/`

### Como adicionar
```bash
npx shadcn@latest add button
npx shadcn@latest add input
npx shadcn@latest add dialog
```

- O CLI gera `src/components/ui/<Component>.tsx`.
- Arquivo é **versionado no repo** — é seu. Customize livremente.
- **Sempre via CLI** na primeira vez. Depois, edita à vontade.

### Customizações
- Documente **qualquer customização não-trivial** com comentário curto no topo do arquivo:
  ```tsx
  // Customizado: variant "destructive-ghost" adicionada (não vem do shadcn).
  ```
- Variantes via **`class-variance-authority`** (já vem com shadcn).

### Não usar lib externa concorrente
Sem `@radix-ui` direto fora do que o shadcn instala. Sem `@material-ui`, `@chakra-ui`, `antd`. **shadcn é o caminho único.**

---

## 3. Layout — `components/layout/`

A estrutura visual do app autenticado entra no Bloco 1. Componentes esperados:

- **`AppShell`** — layout raiz com sidebar + topbar + outlet.
- **`Sidebar`** — navegação principal por área (RH, Folha, Relatórios, Config).
- **`Topbar`** — busca, notificações, usuário.
- **`PageHeader`** — title + breadcrumb + ações da página.
- **`Container`** — wrapper de largura/padding consistente.

**Regra:** layout **não** consulta API direto (exceto `Topbar` para perfil do usuário, via hook centralizado).

---

## 4. Componentes de domínio — `components/<area>/`

Espelham o domínio do backend:

```
src/components/
├── people/
│   ├── ServidorCard.tsx          ← cartão resumo do servidor
│   ├── ServidorList.tsx          ← tabela/lista
│   ├── ServidorForm.tsx          ← formulário create/edit
│   ├── VinculoList.tsx
│   └── DependenteForm.tsx
├── payroll/
│   ├── FolhaCard.tsx
│   ├── HoleriteViewer.tsx
│   ├── RubricaForm.tsx
│   └── LancamentoTable.tsx
└── reports/
    └── RelatorioCard.tsx
```

**Regras:**
- **Naming:** `<Modelo><Tipo>` — `ServidorList`, `ServidorForm`, `ServidorCard`. Tipo padronizado: `Card`, `List`, `Form`, `Detail`, `Header`, `Filter`, `Picker`.
- **Props tipadas** com `interface <Componente>Props`. Sem `any`.
- **Recebe dados via props** quando possível (componente "burro"). Componente que busca dados próprio usa o sufixo `Container` ou tem a lógica em hook isolado.
- **Sem `useEffect` para buscar dados** — usar TanStack Query via hook (`useServidor`, `useServidores`).

---

## 5. Esqueleto de componente

### Burro (recebe props)
```tsx
import { cn } from "@/lib/utils";

interface ServidorCardProps {
  servidor: Servidor;
  onClick?: (id: number) => void;
  className?: string;
}

export function ServidorCard({ servidor, onClick, className }: ServidorCardProps) {
  return (
    <button
      type="button"
      onClick={() => onClick?.(servidor.id)}
      className={cn(
        "rounded-lg border bg-card p-4 text-left transition hover:bg-accent",
        className,
      )}
    >
      <p className="text-sm text-muted-foreground">Matrícula {servidor.matricula}</p>
      <h3 className="font-semibold">{servidor.nome}</h3>
    </button>
  );
}
```

### Esperto (usa hook)
```tsx
import { useServidores } from "@/hooks/useServidores";
import { ServidorCard } from "@/components/people/ServidorCard";
import { LoadingState } from "@/components/feedback/LoadingState";
import { ErrorState } from "@/components/feedback/ErrorState";

interface ServidorListProps {
  search?: string;
  onSelect?: (id: number) => void;
}

export function ServidorList({ search, onSelect }: ServidorListProps) {
  const { data, isLoading, isError, error } = useServidores({ search });

  if (isLoading) return <LoadingState />;
  if (isError) return <ErrorState error={error} />;
  if (!data || data.results.length === 0) {
    return <p className="text-muted-foreground">Nenhum servidor encontrado.</p>;
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {data.results.map((s) => (
        <ServidorCard key={s.id} servidor={s} onClick={onSelect} />
      ))}
    </div>
  );
}
```

---

## 6. Convenções

### Export
- **Named export** preferido (`export function Foo()`), exceto **páginas** que usam `export default` para lazy.
- Um componente por arquivo (componente principal). Pequenos auxiliares no mesmo arquivo são ok se específicos.

### Props
- `interface <Componente>Props` — sempre.
- `children` tipado como `React.ReactNode`.
- **Eventos prefixados com `on`:** `onClick`, `onSelect`, `onSubmit`.
- **Boolean prefixado com adjetivo claro:** `disabled`, `loading`, `compact`. Não `isFoo` (verboso pra prop).
- Usar `?` para opcionais; **não** `| undefined` em prop type explícito.

### Composição vs herança
- React não tem herança útil. **Composição sempre** (children, render-props, slots via prop).
- Para variantes, usar `cva` (class-variance-authority).

### Memo, useMemo, useCallback
- **Não otimizar prematuramente.** React 18 + dev tools mostram hot paths se houver problema.
- Aplicar **só quando há causa medida** (re-render mensurável, lista grande virtualizada).

### Estilo
- Tailwind direto no JSX (ver [`frontend/CONTEXT.md`](../../CONTEXT.md) §6).
- Composição com `cn()`.
- **Nunca** `style={{ ... }}` exceto valores dinâmicos calculados (ex: largura de progresso baseada em prop).

---

## 7. Diretório `feedback/` (a criar no Bloco 1)

Componentes transversais de estado de UI, usados por páginas e listas:

```
src/components/feedback/
├── LoadingState.tsx          ← spinner ou skeleton genérico
├── ErrorState.tsx            ← erro com retry
├── EmptyState.tsx            ← lista vazia com CTA
└── Toast/                    ← (a partir do shadcn `sonner` ou `toast`)
```

Padrão de uso ilustrado em `src/pages/CONTEXT.md` §5 e §11.

---

## 8. Componentes que **não** vão aqui

- **Páginas** → `src/pages/` (ver `pages/CONTEXT.md`).
- **Hooks** → `src/hooks/` (Bloco 1+).
- **Utilitários puros** (formatação, parsing) → `src/lib/`.
- **Tipos compartilhados** → `src/types/` (a criar quando crescer; até lá, dentro do hook que define o tipo).

---

## 9. Acessibilidade no componente

Repassando do `frontend/CONTEXT.md`:

- Botão é `<button>`. Card clicável é `<button>` ou `<a>` (com href real ou `to` do Link).
- Input tem `<label htmlFor>`.
- Diálogos via shadcn `Dialog` (foco trap + ARIA prontos).
- `aria-live="polite"` para feedbacks de operação assíncrona (toast, "Salvando...").
- Contraste AA mínimo.

---

## 10. Testes de componente

- Co-localizar: `ServidorCard.tsx` + `ServidorCard.test.tsx`.
- Foco: **interação observável** (clique chama callback, prop renderiza texto, estado disabled).
- **Não testar implementação interna** (state local, useEffect ordem).

```tsx
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { ServidorCard } from "./ServidorCard";

const servidor = { id: 1, matricula: "0001", nome: "João Silva", cpf: "...", ativo: true };

describe("ServidorCard", () => {
  it("mostra matricula e nome", () => {
    render(<ServidorCard servidor={servidor} />);
    expect(screen.getByText("João Silva")).toBeInTheDocument();
    expect(screen.getByText(/0001/)).toBeInTheDocument();
  });

  it("dispara onClick com o id", async () => {
    const onClick = vi.fn();
    render(<ServidorCard servidor={servidor} onClick={onClick} />);
    await userEvent.click(screen.getByRole("button", { name: /joão silva/i }));
    expect(onClick).toHaveBeenCalledWith(1);
  });
});
```

---

## 11. Storybook?

**Decisão diferida.** Avaliar no Bloco 7 (diferenciação) se o time crescer e UX virar centro de gravidade. Até lá: testes + dev local com `npm run dev` + páginas dedicadas de showcase se necessário.

---

## 12. Checklist antes de commitar componente

- [ ] Está na pasta certa (`ui/` x `layout/` x `<dominio>/`).
- [ ] Naming consistente (`<Modelo><Tipo>` em domínio).
- [ ] Props com `interface`, sem `any`.
- [ ] Tailwind + `cn` (sem CSS-in-JS, sem `style` literal).
- [ ] Acessibilidade básica (semântica + foco + label).
- [ ] Texto em português; identificadores em inglês.
- [ ] Teste co-localizado cobrindo render + interação principal.
- [ ] Entrada no `CHANGELOG.md`.
- [ ] `npm run lint && npm run format:check && npm test` verdes.
