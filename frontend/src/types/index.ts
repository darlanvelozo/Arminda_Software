/**
 * Aliases para os tipos gerados por openapi-typescript (ADR-0008).
 *
 * NUNCA escreva `interface Servidor { ... }` à mão.
 * Tudo deriva de `components["schemas"][...]` ou `paths[...]`.
 *
 * Após mudar serializers no backend, rode `npm run gen:types`.
 */

import type { components, paths } from "./api";

export type { components, paths };

// ============================================================
// Domínio: People
// ============================================================

export type Cargo = components["schemas"]["CargoList"];
export type CargoDetail = components["schemas"]["CargoDetail"];
export type CargoWrite = components["schemas"]["CargoWrite"];

export type Lotacao = components["schemas"]["LotacaoList"];
export type LotacaoDetail = components["schemas"]["LotacaoDetail"];
export type LotacaoWrite = components["schemas"]["LotacaoWrite"];

export type Servidor = components["schemas"]["ServidorList"];
export type ServidorDetail = components["schemas"]["ServidorDetail"];
export type ServidorWrite = components["schemas"]["ServidorWrite"];

export type Vinculo = components["schemas"]["VinculoList"];
export type VinculoDetail = components["schemas"]["VinculoDetail"];
export type VinculoWrite = components["schemas"]["VinculoWrite"];

export type Dependente = components["schemas"]["DependenteList"];
export type DependenteDetail = components["schemas"]["DependenteDetail"];
export type DependenteWrite = components["schemas"]["DependenteWrite"];

export type Documento = components["schemas"]["DocumentoList"];

// ============================================================
// Ações de RH (input dos endpoints @action)
// ============================================================

export type AdmissaoInput = components["schemas"]["AdmissaoInput"];
export type DesligamentoInput = components["schemas"]["DesligamentoInput"];
export type TransferenciaInput = components["schemas"]["TransferenciaInput"];

// ============================================================
// Domínio: Payroll
// ============================================================

export type Rubrica = components["schemas"]["RubricaList"];
export type RubricaDetail = components["schemas"]["RubricaDetail"];
export type RubricaWrite = components["schemas"]["RubricaWrite"];

// ============================================================
// Auth (TokenObtainPair acumula request+response em drf-spectacular)
// ============================================================

export type TokenPair = components["schemas"]["ArmindaTokenObtainPair"];
export type TokenRefresh = components["schemas"]["TokenRefresh"];

/**
 * Input do POST /api/auth/login/.
 * Apenas e-mail e senha — drf-spectacular nao deriva subset, entao tipamos
 * explicitamente o request body do login.
 */
export interface LoginRequest {
  email: string;
  password: string;
}

/**
 * Output completo do login. drf-spectacular nao tipa o campo `user` que
 * vem da nossa serializacao customizada (UserMeSerializer); descrevemos
 * aqui — a unica fonte da verdade desse shape e
 * `apps/core/auth/serializers.py:UserMeSerializer`.
 */
export interface LoginResponse {
  access: string;
  refresh: string;
  user: UserMe;
}

/**
 * Tipagem manual de UserMe (saida de /api/auth/me/ + payload de login).
 * drf-spectacular nao tipa o response porque `MeView` e APIView simples
 * sem serializer_class. Resolver no backend com @extend_schema (TODO).
 */
export interface UserMe {
  id: number;
  email: string;
  nome_completo: string;
  first_name: string;
  last_name: string;
  is_staff: boolean;
  is_superuser: boolean;
  precisa_trocar_senha: boolean;
  municipios: PapelEmMunicipio[];
}

export interface PapelEmMunicipio {
  schema: string;
  codigo_ibge: string;
  nome: string;
  uf: string;
  papel: string;
}

// ============================================================
// Histórico (simple-history) — também não tipado pelo drf-spectacular
// ============================================================

export interface HistoricoServidorEntry {
  history_id: number;
  history_date: string;
  history_type: "+" | "~" | "-";
  history_change_reason: string | null;
  history_user_email: string | null;
  matricula: string;
  nome: string;
  cpf: string;
  ativo: boolean;
}

// ============================================================
// Paginação genérica (drf-spectacular gera Paginated*List por modelo;
// este tipo é usado quando reusamos hooks)
// ============================================================

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

// ============================================================
// Erros de domínio (formato HTTP 400 que o backend envia)
// ============================================================

export interface DomainErrorResponse {
  detail: string;
  code: string;
}
