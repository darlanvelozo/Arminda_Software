/**
 * Hooks TanStack Query para o recurso Cargo (Bloco 1.3b).
 *
 * Endpoints (tenant — exigem header X-Tenant, anexado pelo interceptor):
 *   GET    /api/people/cargos/                   listagem paginada
 *   GET    /api/people/cargos/{id}/              detalhe
 *   POST   /api/people/cargos/                   create
 *   PATCH  /api/people/cargos/{id}/              update parcial
 *   DELETE /api/people/cargos/{id}/              destroy
 *
 * Filtros suportados pelo backend:
 *   ?search=...         busca em codigo/nome/cbo (DRF SearchFilter)
 *   ?ordering=nome      ou -nome / codigo / -codigo / criado_em / -criado_em
 *   ?ativo=true|false   filtro por ativo
 *   ?nivel_escolaridade=fundamental|medio|...
 *   ?page=N             paginação default DRF
 */

import { useMutation, useQuery, useQueryClient, keepPreviousData } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Cargo, CargoDetail, CargoWrite, Paginated } from "@/types";

/**
 * Payload de escrita: o tipo gerado pelo openapi-typescript marca `id` como
 * required-readonly (limitação do drf-spectacular para read_only_fields), mas
 * não enviamos `id` em POST/PATCH.
 */
export type CargoInput = Omit<CargoWrite, "id">;

export interface CargosListParams {
  search?: string;
  ativo?: boolean;
  nivelEscolaridade?: string;
  ordering?: string;
  page?: number;
}

const BASE = "/people/cargos/";

// ============================================================
// Query keys (escopadas por tenant para evitar mistura entre municípios)
// ============================================================

const cargosKey = (tenant: string | null) => ["cargos", tenant] as const;
const cargosListKey = (tenant: string | null, params: CargosListParams) =>
  [...cargosKey(tenant), "list", params] as const;
const cargoDetailKey = (tenant: string | null, id: number) =>
  [...cargosKey(tenant), "detail", id] as const;

// ============================================================
// Fetchers
// ============================================================

async function fetchCargos(params: CargosListParams): Promise<Paginated<Cargo>> {
  const { data } = await api.get<Paginated<Cargo>>(BASE, {
    params: {
      search: params.search || undefined,
      ativo: params.ativo,
      nivel_escolaridade: params.nivelEscolaridade || undefined,
      ordering: params.ordering || undefined,
      page: params.page || undefined,
    },
  });
  return data;
}

async function fetchCargo(id: number): Promise<CargoDetail> {
  const { data } = await api.get<CargoDetail>(`${BASE}${id}/`);
  return data;
}

async function createCargo(payload: CargoInput): Promise<CargoDetail> {
  const { data } = await api.post<CargoDetail>(BASE, payload);
  return data;
}

async function updateCargo(id: number, payload: Partial<CargoInput>): Promise<CargoDetail> {
  const { data } = await api.patch<CargoDetail>(`${BASE}${id}/`, payload);
  return data;
}

async function deleteCargo(id: number): Promise<void> {
  await api.delete(`${BASE}${id}/`);
}

// ============================================================
// Hooks
// ============================================================

export function useCargosList(params: CargosListParams) {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: cargosListKey(activeTenant, params),
    queryFn: () => fetchCargos(params),
    enabled: !!activeTenant,
    placeholderData: keepPreviousData,
  });
}

export function useCargo(id: number | null) {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: cargoDetailKey(activeTenant, id ?? 0),
    queryFn: () => fetchCargo(id as number),
    enabled: !!activeTenant && id !== null,
  });
}

export function useCreateCargo() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createCargo,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: cargosKey(activeTenant) });
    },
  });
}

export function useUpdateCargo() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<CargoInput> }) =>
      updateCargo(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: cargosKey(activeTenant) });
    },
  });
}

export function useDeleteCargo() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteCargo,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: cargosKey(activeTenant) });
    },
  });
}
