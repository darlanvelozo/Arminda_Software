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
  natureza?: string;
  cadastroIncompleto?: boolean;
  ordering?: string;
  page?: number;
  pageSize?: number;
}

// ============================================================
// Onda 1.6b — qualidade cadastral, bulk-update e importer CSV
// ============================================================

export interface QualidadeCampoFaltante {
  campo: string;
  label: string;
}

export interface QualidadeServidor {
  servidor_id: number;
  matricula: string;
  nome: string;
  total_campos: number;
  campos_preenchidos: number;
  campos_faltantes: QualidadeCampoFaltante[];
  score: number;
  completo: boolean;
}

export interface QualidadeBreakdownEntry {
  campo: string;
  label: string;
  servidores_pendentes: number;
}

export interface QualidadeResumo {
  total_servidores: number;
  completos: number;
  incompletos: number;
  score_medio: number;
  breakdown_campos_faltantes: QualidadeBreakdownEntry[];
}

export interface BulkUpdateResult {
  atualizados: number;
  ids_nao_encontrados: number[];
  total_solicitado: number;
}

export interface BulkUpdateServidoresPayload {
  servidor_ids: number[];
  updates: Record<string, unknown>;
}

export interface BulkUpdateVinculosPayload {
  vinculo_ids: number[];
  updates: Record<string, unknown>;
}

export interface ImportCsvPreview {
  linha: number;
  identificador: string;
  servidor_id: number | null;
  antes: Record<string, unknown>;
  depois: Record<string, unknown>;
}

export interface ImportCsvResultado {
  total_linhas: number;
  atualizados: number;
  ignorados_servidor_nao_encontrado: number;
  ignorados_sem_mudanca: number;
  erros: { linha: number; mensagem: string }[];
  preview: ImportCsvPreview[];
  colunas_aceitas_mapeadas: string[];
  colunas_ignoradas: string[];
  dry_run?: boolean;
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
      natureza: params.natureza || undefined,
      cadastro_incompleto: params.cadastroIncompleto,
      ordering: params.ordering || undefined,
      page: params.page || undefined,
      page_size: params.pageSize || undefined,
    },
  });
  return data;
}

async function fetchQualidadeResumo(): Promise<QualidadeResumo> {
  const { data } = await api.get<QualidadeResumo>(`${BASE}qualidade-resumo/`);
  return data;
}

async function fetchQualidadeServidor(id: number): Promise<QualidadeServidor> {
  const { data } = await api.get<QualidadeServidor>(`${BASE}${id}/qualidade/`);
  return data;
}

async function bulkUpdateServidores(
  payload: BulkUpdateServidoresPayload,
): Promise<BulkUpdateResult> {
  const { data } = await api.post<BulkUpdateResult>(`${BASE}bulk-update/`, payload);
  return data;
}

async function bulkUpdateVinculos(
  payload: BulkUpdateVinculosPayload,
): Promise<BulkUpdateResult> {
  const { data } = await api.post<BulkUpdateResult>(`/people/vinculos/bulk-update/`, payload);
  return data;
}

async function importarServidoresCsv(args: {
  file: File;
  colunaIdentificador: "matricula" | "cpf";
  dryRun: boolean;
}): Promise<ImportCsvResultado> {
  const form = new FormData();
  form.append("arquivo", args.file);
  form.append("coluna_identificador", args.colunaIdentificador);
  form.append("dry_run", args.dryRun ? "true" : "false");
  const { data } = await api.post<ImportCsvResultado>(
    "/imports/csv/servidores/",
    form,
    { headers: { "Content-Type": "multipart/form-data" } },
  );
  return data;
}

async function fetchServidor(id: number): Promise<ServidorDetail> {
  const { data } = await api.get<ServidorDetail>(`${BASE}${id}/`);
  return data;
}

async function fetchHistorico(id: number): Promise<HistoricoServidorEntry[]> {
  // O endpoint pode vir paginado (DRF default { count, results, ... }) ou
  // como array direto, dependendo da configuração do paginator no viewset.
  // Aceitamos ambos para evitar runtime error no consumidor.
  const { data } = await api.get<
    HistoricoServidorEntry[] | { results: HistoricoServidorEntry[] }
  >(`${BASE}${id}/historico/`);
  if (Array.isArray(data)) return data;
  return data.results ?? [];
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

export interface DesligamentoPayload {
  data_desligamento: string;
  motivo?: string;
  // Rescisão estruturada (Onda 3.2)
  motivo_demissao?: string;
  aviso_previo_indenizado?: boolean;
  tem_ferias_vencidas?: boolean;
  saldo_fgts?: string;
}

async function desligarServidor(
  id: number,
  payload: DesligamentoPayload,
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
      payload: DesligamentoPayload;
    }) => desligarServidor(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: servidoresKey(activeTenant) }),
  });
}

// ============================================================
// Onda 1.6b — qualidade, bulk, importer
// ============================================================

export function useQualidadeResumo() {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: [...servidoresKey(activeTenant), "qualidade-resumo"] as const,
    queryFn: fetchQualidadeResumo,
    enabled: !!activeTenant,
  });
}

export function useQualidadeServidor(id: number | null) {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: [...servidoresKey(activeTenant), "qualidade", id ?? 0] as const,
    queryFn: () => fetchQualidadeServidor(id as number),
    enabled: !!activeTenant && id !== null,
  });
}

export function useBulkUpdateServidores() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: bulkUpdateServidores,
    onSuccess: () => qc.invalidateQueries({ queryKey: servidoresKey(activeTenant) }),
  });
}

export function useBulkUpdateVinculos() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: bulkUpdateVinculos,
    onSuccess: () => qc.invalidateQueries({ queryKey: servidoresKey(activeTenant) }),
  });
}

export function useImportarServidoresCsv() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: importarServidoresCsv,
    onSuccess: () => qc.invalidateQueries({ queryKey: servidoresKey(activeTenant) }),
  });
}
