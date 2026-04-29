# ADR-0008 — Geração de tipos TypeScript a partir do schema OpenAPI

**Status:** Aceito
**Data:** 2026-04-29
**Bloco:** 1.3 (Frontend autenticado)
**Depende de:** [ADR-0003](0003-vite-react-frontend.md), [ADR-0007](0007-jwt-rbac.md)

## Contexto

O backend Arminda expõe um schema OpenAPI completo via `drf-spectacular` em
`/api/schema/` (renderizado em `/api/docs/` e `/api/redoc/`). Cada serializer
DRF tem campos tipados, choices, e marcações de obrigatoriedade.

O frontend, ao consumir esses endpoints, precisa de **tipos TypeScript**
para os request/response payloads. Há três caminhos:

1. **Tipar manualmente** — escrever `interface Servidor { matricula: string; ... }`
   à mão, em paralelo aos serializers Python.
2. **Tipar parcial via codegen** — usar bibliotecas como `openapi-fetch`,
   `swagger-typescript-api` ou `orval` para gerar cliente + tipos.
3. **Apenas tipos** via `openapi-typescript` — gera **só** os types do schema,
   sem cliente HTTP. O cliente continua sendo o `api.ts` (axios) já existente.

## Decisão

Adotar **`openapi-typescript`** + script `npm run gen:types`.

- Gera **um único arquivo** `frontend/src/types/api.ts` com types nomeados
  por endpoint e schema.
- **Não substitui** o cliente axios existente — o cliente continua em
  `src/lib/api.ts` e os hooks consumem os types gerados.
- Roda **sob demanda** (não no build), evitando dependência circular do
  backend rodando para o frontend buildar.
- Geração apontada para `http://localhost:8000/api/schema/` em dev.
  Em CI, gera contra um snapshot do schema commitado.

## Como rodar

```bash
# Requer backend rodando em :8000
cd frontend
npm run gen:types
# -> escreve src/types/api.ts
```

Para CI / build offline (a configurar no Bloco 1.3 hardening):
- Snapshot do schema em `frontend/openapi-schema.json` (commitado).
- Script `gen:types:offline` que lê desse snapshot.
- Workflow CI valida que `gen:types --check` não detecta divergência
  entre snapshot e schema servido.

## Convenções de uso

```ts
// Antes (tipos manuais — proibido em codigo novo a partir desta ADR):
interface Servidor {
  id: number;
  matricula: string;
  nome: string;
}

// Depois:
import type { components } from "@/types/api";
type Servidor = components["schemas"]["ServidorList"];
type ServidorDetail = components["schemas"]["ServidorDetail"];
type AdmissaoInput = components["schemas"]["AdmissaoInput"];

// Com `paths`:
type ListServidoresResponse =
  paths["/api/people/servidores/"]["get"]["responses"]["200"]["content"]["application/json"];
```

Para evitar boilerplate, criar **alias re-exports** em
`src/types/index.ts`:

```ts
export type { components, paths } from "./api";
import type { components } from "./api";

export type Servidor = components["schemas"]["ServidorList"];
export type ServidorDetail = components["schemas"]["ServidorDetail"];
export type AdmissaoInput = components["schemas"]["AdmissaoInput"];
// ... outros tipos de domínio
```

## Consequências

**Positivas**
- **Zero dessincronização** entre serializer e tipo TS. Mudou um campo no
  backend? Roda `gen:types` e o `tsc` apontará todos os pontos quebrados
  no frontend.
- **Documentação viva**: o IntelliSense conhece todos os campos,
  choices, formatos.
- **Refactor seguro**: rename de campo no backend → erro de compilação
  no frontend.
- **Sem cliente HTTP gerado** — preservamos `api.ts` (axios) com nossos
  interceptors customizados (JWT + X-Tenant).

**Negativas / mitigações**
- **Dependência runtime**: gerar requer backend rodando. Mitigação:
  snapshot commitado + `gen:types:offline`.
- **Tipos verbosos**: `components["schemas"]["X"]` é feio. Mitigação:
  `src/types/index.ts` faz aliases.
- **Choices viram `string`** (não union literal) por default. Mitigação:
  configurar `--enum` no `openapi-typescript` para gerar uniões literais
  quando o schema tem `enum`.
- **drf-spectacular** às vezes gera nomes longos para serializers
  inline. Mitigação: usar `@extend_schema` no backend para nomear
  componentes.

## Alternativas consideradas

- **`swagger-typescript-api`** — gera cliente + types. Descartado:
  preferimos manter axios + TanStack Query nosso, sem mais um cliente
  para coordenar.
- **`orval`** — gera React Query hooks tipados a partir do schema.
  Atraente, mas força o padrão dos hooks do orval, que é diferente do
  nosso (`useServidores`, `useAdmitirServidor`). Descartado para
  preservar liberdade.
- **`openapi-fetch`** — substituiria axios. Descartado: `axios` já está
  configurado com interceptors estáveis; trocar nesta etapa é fricção
  sem ganho real.
- **Tipos manuais** — descartado: dessincronização inevitável a longo
  prazo (16k servidores em produção, sem espaço para drift).

## Implicações para o desenvolvimento

- `frontend/CONTEXT.md` §4 atualizado: "Tipos vêm do schema OpenAPI —
  proibido tipar à mão".
- Pre-commit ou lint rule (futuro) que avisa quando `interface`
  duplica algo já em `components["schemas"]`.
- ADRs futuras de mudança de contrato API devem mencionar impacto
  no `gen:types` do frontend.

## Referências

- [openapi-typescript](https://openapi-ts.dev/)
- [drf-spectacular](https://drf-spectacular.readthedocs.io/)
- ADR-0007 (JWT + RBAC) define endpoints de auth
