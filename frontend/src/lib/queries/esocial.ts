/**
 * Hooks TanStack Query para eventos do eSocial (Onda 4.1).
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { CertificadoDigital, EventoESocial, Paginated } from "@/types";

export interface GerarEventoInput {
  tipo: "S-1000" | "S-1005" | "S-1010";
  orgao_emissor: number;
  rubrica?: number;
  competencia?: string;
  class_trib?: string;
}

const BASE = "/esocial/eventos/";
const key = (tenant: string | null) => ["esocial-eventos", tenant] as const;

export function useEventosEsocial() {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: key(activeTenant),
    queryFn: async () => {
      const { data } = await api.get<Paginated<EventoESocial>>(BASE, {
        params: { page_size: 200, ordering: "-criado_em" },
      });
      return data;
    },
    enabled: !!activeTenant,
  });
}

export function useGerarEvento() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: GerarEventoInput) => {
      const { data } = await api.post<EventoESocial>(`${BASE}gerar/`, payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: key(activeTenant) }),
  });
}

export function useAssinarEvento() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      const { data } = await api.post<EventoESocial>(`${BASE}${id}/assinar/`);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: key(activeTenant) }),
  });
}

// ---- Cofre de certificados (Onda 4.2) ----
const CERT_BASE = "/esocial/certificados/";
const certKey = (tenant: string | null) => ["esocial-certificados", tenant] as const;

export function useCertificados() {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: certKey(activeTenant),
    queryFn: async () => {
      const { data } = await api.get<Paginated<CertificadoDigital>>(CERT_BASE, {
        params: { page_size: 200 },
      });
      return data;
    },
    enabled: !!activeTenant,
  });
}

export function useUploadCertificado() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (vars: { orgao_emissor: number; arquivo: File; senha: string }) => {
      const fd = new FormData();
      fd.append("orgao_emissor", String(vars.orgao_emissor));
      fd.append("arquivo", vars.arquivo);
      fd.append("senha", vars.senha);
      const { data } = await api.post<CertificadoDigital>(`${CERT_BASE}upload/`, fd);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: certKey(activeTenant) }),
  });
}

/** Dispara o download do XML do evento (endpoint `baixar`). */
export async function baixarEventoXml(id: number, idEvento: string) {
  const { data } = await api.get(`${BASE}${id}/baixar/`, { responseType: "blob" });
  const url = window.URL.createObjectURL(data as Blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${idEvento}.xml`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}
