/**
 * Hooks TanStack Query para Documentos digitalizados (Onda 1.5).
 *
 * Endpoints:
 *   GET    /api/people/documentos/?servidor=<id>     lista filtrada
 *   POST   /api/people/documentos/                   upload (multipart/form-data)
 *   DELETE /api/people/documentos/{id}/              destroy
 *
 * Upload via FormData — content-type especial; axios deixa o navegador
 * preencher o boundary.
 */

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Documento, Paginated } from "@/types";

export interface DocumentoUploadInput {
  servidor: number;
  tipo: string;
  descricao: string;
  arquivo: File;
}

const BASE = "/people/documentos/";

const documentosKey = (tenant: string | null) => ["documentos", tenant] as const;

async function fetchDocumentos(servidorId: number): Promise<Paginated<Documento>> {
  const { data } = await api.get<Paginated<Documento>>(BASE, {
    params: { servidor: servidorId, ordering: "-data_upload" },
  });
  return data;
}

async function uploadDocumento(payload: DocumentoUploadInput): Promise<Documento> {
  const form = new FormData();
  form.append("servidor", String(payload.servidor));
  form.append("tipo", payload.tipo);
  form.append("descricao", payload.descricao);
  form.append("arquivo", payload.arquivo);
  const { data } = await api.post<Documento>(BASE, form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

async function deleteDocumento(id: number): Promise<void> {
  await api.delete(`${BASE}${id}/`);
}

export function useDocumentosDoServidor(servidorId: number | null) {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: [...documentosKey(activeTenant), "by-servidor", servidorId ?? 0],
    queryFn: () => fetchDocumentos(servidorId as number),
    enabled: !!activeTenant && servidorId !== null,
    placeholderData: keepPreviousData,
  });
}

export function useUploadDocumento() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: uploadDocumento,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: documentosKey(activeTenant) });
      qc.invalidateQueries({ queryKey: ["servidores", activeTenant] });
    },
  });
}

export function useDeleteDocumento() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteDocumento,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: documentosKey(activeTenant) });
      qc.invalidateQueries({ queryKey: ["servidores", activeTenant] });
    },
  });
}
