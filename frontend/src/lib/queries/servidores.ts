/**
 * Hooks TanStack Query para Servidor + ações relacionadas (Bloco 1.3b).
 *
 * Endpoints (todos tenant — exigem X-Tenant):
 *   GET    /api/people/servidores/                  list
 *   GET    /api/people/servidores/{id}/             detalhe (com vinculos + dependentes embutidos)
 *   PATCH  /api/people/servidores/{id}/             update parcial
 *   GET    /api/people/servidores/{id}/historico/   simple-history
 *   POST   /api/people/servidores/admitir/          cria servidor + vínculo (atômico)
 *   POST   /api/people/servidores/{id}/desligar/    encerra todos vínculos + inativa
 *
 * Filtros backend:
 *   ?search=...       (matricula/nome/cpf)
 *   ?ordering=nome|matricula|criado_em
 *   ?ativo=true|false
 *   ?sexo=M|F
 *   ?cargo=<id>       (vincula via vinculos__cargo)
 *   ?lotacao=<id>
 *   ?regime=estatutario|...
 */

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type {
  AdmissaoInput,
  HistoricoServidorEntry,
  Paginated,
  Servidor,
  ServidorDetail,
  ServidorWrite,
} from "@/types";

export type ServidorInput = Omit<ServidorWrite, "id">;

export interface ServidoresListParams {
  search?: string;
  ativo?: boolean;
  sexo?: "M" | "F";
  cargoId?: number;
  lotacaoId?: number;
  regime?: string;
  ordering?: string;
  page?: number;
}

const BASE = "/people/servidores/";

const servidoresKey = (tenant: string | null) => ["servidores", tenant] as const;
const servidoresListKey = (tenant: string | null, params: ServidoresListParams) =>
  [...servidoresKey(tenant), "list", params] as const;
const servidorDetailKey = (tenant: string | null, id: number) =>
  [...servidoresKey(tenant), "detail", id] as const;
const servidorHistoricoKey = (tenant: string | null, id: number) =>
  [...servidoresKey(tenant), "historico", id] as const;

async function fetchServidores(params: ServidoresListParams): Promise<Paginated<Servidor>> {
  const { data } = await api.get<Paginated<Servidor>>(BASE, {
    params: {
      search: params.search || undefined,
      ativo: params.ativo,
      sexo: params.sexo,
      cargo: params.cargoId,
      lotacao: params.lotacaoId,
      regime: params.regime || undefined,
      ordering: params.ordering || undefined,
      page: params.page || undefined,
    },
  });
  return data;
}

async function fetchServidor(id: number): Promise<ServidorDetail> {
  const { data } = await api.get<ServidorDetail>(`${BASE}${id}/`);
  return data;
}

async function fetchHistorico(id: number): Promise<HistoricoServidorEntry[]> {
  const { data } = await api.get<HistoricoServidorEntry[]>(`${BASE}${id}/historico/`);
  return data;
}

async function admitirServidor(payload: AdmissaoInput): Promise<ServidorDetail> {
  const { data } = await api.post<ServidorDetail>(`${BASE}admitir/`, payload);
  return data;
}

async function updateServidor(
  id: number,
  payload: Partial<ServidorInput>,
): Promise<ServidorDetail> {
  const { data } = await api.patch<ServidorDetail>(`${BASE}${id}/`, payload);
  return data;
}

async function desligarServidor(
  id: number,
  payload: { data_desligamento: string; motivo?: string },
): Promise<ServidorDetail> {
  const { data } = await api.post<ServidorDetail>(`${BASE}${id}/desligar/`, payload);
  return data;
}

// ============================================================
// Hooks
// ============================================================

export function useServidoresList(params: ServidoresListParams) {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: servidoresListKey(activeTenant, params),
    queryFn: () => fetchServidores(params),
    enabled: !!activeTenant,
    placeholderData: keepPreviousData,
  });
}

export function useServidor(id: number | null) {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: servidorDetailKey(activeTenant, id ?? 0),
    queryFn: () => fetchServidor(id as number),
    enabled: !!activeTenant && id !== null,
  });
}

export function useServidorHistorico(id: number | null) {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: servidorHistoricoKey(activeTenant, id ?? 0),
    queryFn: () => fetchHistorico(id as number),
    enabled: !!activeTenant && id !== null,
  });
}

export function useAdmitirServidor() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: admitirServidor,
    onSuccess: () => qc.invalidateQueries({ queryKey: servidoresKey(activeTenant) }),
  });
}

export function useUpdateServidor() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<ServidorInput> }) =>
      updateServidor(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: servidoresKey(activeTenant) }),
  });
}

export function useDesligarServidor() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      id,
      payload,
    }: {
      id: number;
      payload: { data_desligamento: string; motivo?: string };
    }) => desligarServidor(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: servidoresKey(activeTenant) }),
  });
}
