/**
 * Hooks TanStack Query para Folha + Lançamentos (Onda 2.6).
 *
 * API:
 *   GET    /payroll/folhas/?ano=&mes=&tipo=&status=&search=
 *   GET    /payroll/folhas/{id}/
 *   POST   /payroll/folhas/
 *   PATCH  /payroll/folhas/{id}/
 *   DELETE /payroll/folhas/{id}/
 *   POST   /payroll/folhas/{id}/calcular/   → RelatorioCalculo
 *
 *   GET    /payroll/lancamentos/?folha=&servidor=&rubrica__codigo=&page=
 */

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type {
  Folha,
  FolhaDetail,
  FolhaWrite,
  Lancamento,
  Paginated,
  RelatorioCalculo,
} from "@/types";

export type FolhaInput = Omit<FolhaWrite, "id">;

export interface FolhasListParams {
  ano?: number;
  mes?: number;
  tipo?: string;
  status?: string;
  ordering?: string;
  page?: number;
}

export interface LancamentosListParams {
  folha?: number;
  servidor?: number;
  rubrica?: number;
  rubrica_codigo?: string;
  servidor_nome?: string;
  ordering?: string;
  page?: number;
  page_size?: number;
}

const FOLHAS = "/payroll/folhas/";
const LANCAMENTOS = "/payroll/lancamentos/";

const folhasKey = (tenant: string | null) => ["folhas", tenant] as const;
const folhasListKey = (tenant: string | null, params: FolhasListParams) =>
  [...folhasKey(tenant), "list", params] as const;
const folhaDetailKey = (tenant: string | null, id: number) =>
  [...folhasKey(tenant), "detail", id] as const;
const lancamentosKey = (tenant: string | null) => ["lancamentos", tenant] as const;
const lancamentosListKey = (tenant: string | null, params: LancamentosListParams) =>
  [...lancamentosKey(tenant), "list", params] as const;

// ============================================================
// Fetchers
// ============================================================

async function fetchFolhas(params: FolhasListParams): Promise<Paginated<Folha>> {
  const { data } = await api.get<Paginated<Folha>>(FOLHAS, {
    params: {
      ano: params.ano,
      mes: params.mes,
      tipo: params.tipo,
      status: params.status,
      ordering: params.ordering || "-competencia",
      page: params.page,
    },
  });
  return data;
}

async function fetchFolha(id: number): Promise<FolhaDetail> {
  const { data } = await api.get<FolhaDetail>(`${FOLHAS}${id}/`);
  return data;
}

async function createFolha(payload: FolhaInput): Promise<FolhaDetail> {
  const { data } = await api.post<FolhaDetail>(FOLHAS, payload);
  return data;
}

async function updateFolha(id: number, payload: Partial<FolhaInput>): Promise<FolhaDetail> {
  const { data } = await api.patch<FolhaDetail>(`${FOLHAS}${id}/`, payload);
  return data;
}

async function deleteFolha(id: number): Promise<void> {
  await api.delete(`${FOLHAS}${id}/`);
}

async function calcularFolha(id: number): Promise<RelatorioCalculo> {
  const { data } = await api.post<RelatorioCalculo>(`${FOLHAS}${id}/calcular/`);
  return data;
}

async function fetchLancamentos(
  params: LancamentosListParams,
): Promise<Paginated<Lancamento>> {
  const { data } = await api.get<Paginated<Lancamento>>(LANCAMENTOS, {
    params: {
      folha: params.folha,
      servidor: params.servidor,
      rubrica: params.rubrica,
      rubrica_codigo: params.rubrica_codigo,
      servidor_nome: params.servidor_nome,
      ordering: params.ordering || "servidor__nome,rubrica__codigo",
      page: params.page,
      page_size: params.page_size,
    },
  });
  return data;
}

// ============================================================
// Hooks
// ============================================================

export function useFolhasList(params: FolhasListParams) {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: folhasListKey(activeTenant, params),
    queryFn: () => fetchFolhas(params),
    enabled: !!activeTenant,
    placeholderData: keepPreviousData,
  });
}

export function useFolha(id: number | null) {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: folhaDetailKey(activeTenant, id ?? 0),
    queryFn: () => fetchFolha(id as number),
    enabled: !!activeTenant && id !== null,
  });
}

export function useCreateFolha() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createFolha,
    onSuccess: () => qc.invalidateQueries({ queryKey: folhasKey(activeTenant) }),
  });
}

export function useUpdateFolha() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<FolhaInput> }) =>
      updateFolha(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: folhasKey(activeTenant) }),
  });
}

export function useDeleteFolha() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteFolha,
    onSuccess: () => qc.invalidateQueries({ queryKey: folhasKey(activeTenant) }),
  });
}

export function useCalcularFolha() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: calcularFolha,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: folhasKey(activeTenant) });
      qc.invalidateQueries({ queryKey: lancamentosKey(activeTenant) });
    },
  });
}

export function useLancamentosList(params: LancamentosListParams) {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: lancamentosListKey(activeTenant, params),
    queryFn: () => fetchLancamentos(params),
    enabled: !!activeTenant && params.folha !== undefined,
    placeholderData: keepPreviousData,
  });
}
