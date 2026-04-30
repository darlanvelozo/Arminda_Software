/**
 * Hooks TanStack Query para o recurso Rubrica (Bloco 1.3b).
 *
 * Filtros backend:
 *   ?search=...                  busca em codigo/nome
 *   ?ordering=nome|codigo
 *   ?ativo=true|false
 *   ?tipo=provento|desconto|informativa
 *   ?incide_inss=true|false      (idem _irrf, _fgts)
 */

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Paginated, Rubrica, RubricaDetail, RubricaWrite } from "@/types";

export type RubricaInput = Omit<RubricaWrite, "id">;

export interface RubricasListParams {
  search?: string;
  ativo?: boolean;
  tipo?: "provento" | "desconto" | "informativa";
  ordering?: string;
  page?: number;
}

const BASE = "/payroll/rubricas/";

const rubricasKey = (tenant: string | null) => ["rubricas", tenant] as const;
const rubricasListKey = (tenant: string | null, params: RubricasListParams) =>
  [...rubricasKey(tenant), "list", params] as const;
const rubricaDetailKey = (tenant: string | null, id: number) =>
  [...rubricasKey(tenant), "detail", id] as const;

async function fetchRubricas(params: RubricasListParams): Promise<Paginated<Rubrica>> {
  const { data } = await api.get<Paginated<Rubrica>>(BASE, {
    params: {
      search: params.search || undefined,
      ativo: params.ativo,
      tipo: params.tipo,
      ordering: params.ordering || undefined,
      page: params.page || undefined,
    },
  });
  return data;
}

async function fetchRubrica(id: number): Promise<RubricaDetail> {
  const { data } = await api.get<RubricaDetail>(`${BASE}${id}/`);
  return data;
}

async function createRubrica(payload: RubricaInput): Promise<RubricaDetail> {
  const { data } = await api.post<RubricaDetail>(BASE, payload);
  return data;
}

async function updateRubrica(id: number, payload: Partial<RubricaInput>): Promise<RubricaDetail> {
  const { data } = await api.patch<RubricaDetail>(`${BASE}${id}/`, payload);
  return data;
}

async function deleteRubrica(id: number): Promise<void> {
  await api.delete(`${BASE}${id}/`);
}

export function useRubricasList(params: RubricasListParams) {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: rubricasListKey(activeTenant, params),
    queryFn: () => fetchRubricas(params),
    enabled: !!activeTenant,
    placeholderData: keepPreviousData,
  });
}

export function useRubrica(id: number | null) {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: rubricaDetailKey(activeTenant, id ?? 0),
    queryFn: () => fetchRubrica(id as number),
    enabled: !!activeTenant && id !== null,
  });
}

export function useCreateRubrica() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createRubrica,
    onSuccess: () => qc.invalidateQueries({ queryKey: rubricasKey(activeTenant) }),
  });
}

export function useUpdateRubrica() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<RubricaInput> }) =>
      updateRubrica(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: rubricasKey(activeTenant) }),
  });
}

export function useDeleteRubrica() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteRubrica,
    onSuccess: () => qc.invalidateQueries({ queryKey: rubricasKey(activeTenant) }),
  });
}
