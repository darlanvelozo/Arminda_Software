/**
 * Hooks TanStack Query para o recurso Lotacao (Bloco 1.3b).
 *
 * Filtros backend:
 *   ?search=...         busca em codigo/nome/sigla
 *   ?ordering=nome      ou -nome / codigo / -codigo / criado_em
 *   ?ativo=true|false
 *   ?raiz=true          apenas lotações sem pai (raízes)
 *   ?lotacao_pai=<id>   filhas diretas de uma lotação
 */

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Lotacao, LotacaoDetail, LotacaoWrite, Paginated } from "@/types";

export type LotacaoInput = Omit<LotacaoWrite, "id">;

export interface LotacoesListParams {
  search?: string;
  ativo?: boolean;
  natureza?: string;
  raiz?: boolean;
  lotacaoPaiId?: number;
  ordering?: string;
  page?: number;
}

const BASE = "/people/lotacoes/";

const lotacoesKey = (tenant: string | null) => ["lotacoes", tenant] as const;
const lotacoesListKey = (tenant: string | null, params: LotacoesListParams) =>
  [...lotacoesKey(tenant), "list", params] as const;
const lotacaoDetailKey = (tenant: string | null, id: number) =>
  [...lotacoesKey(tenant), "detail", id] as const;

async function fetchLotacoes(params: LotacoesListParams): Promise<Paginated<Lotacao>> {
  const { data } = await api.get<Paginated<Lotacao>>(BASE, {
    params: {
      search: params.search || undefined,
      ativo: params.ativo,
      natureza: params.natureza || undefined,
      raiz: params.raiz,
      lotacao_pai: params.lotacaoPaiId,
      ordering: params.ordering || undefined,
      page: params.page || undefined,
    },
  });
  return data;
}

async function fetchLotacao(id: number): Promise<LotacaoDetail> {
  const { data } = await api.get<LotacaoDetail>(`${BASE}${id}/`);
  return data;
}

async function createLotacao(payload: LotacaoInput): Promise<LotacaoDetail> {
  const { data } = await api.post<LotacaoDetail>(BASE, payload);
  return data;
}

async function updateLotacao(id: number, payload: Partial<LotacaoInput>): Promise<LotacaoDetail> {
  const { data } = await api.patch<LotacaoDetail>(`${BASE}${id}/`, payload);
  return data;
}

async function deleteLotacao(id: number): Promise<void> {
  await api.delete(`${BASE}${id}/`);
}

export function useLotacoesList(params: LotacoesListParams) {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: lotacoesListKey(activeTenant, params),
    queryFn: () => fetchLotacoes(params),
    enabled: !!activeTenant,
    placeholderData: keepPreviousData,
  });
}

export function useLotacao(id: number | null) {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: lotacaoDetailKey(activeTenant, id ?? 0),
    queryFn: () => fetchLotacao(id as number),
    enabled: !!activeTenant && id !== null,
  });
}

export function useCreateLotacao() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createLotacao,
    onSuccess: () => qc.invalidateQueries({ queryKey: lotacoesKey(activeTenant) }),
  });
}

export function useUpdateLotacao() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<LotacaoInput> }) =>
      updateLotacao(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: lotacoesKey(activeTenant) }),
  });
}

export function useDeleteLotacao() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteLotacao,
    onSuccess: () => qc.invalidateQueries({ queryKey: lotacoesKey(activeTenant) }),
  });
}
