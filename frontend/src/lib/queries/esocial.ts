/**
 * Hooks TanStack Query para eventos do eSocial (Onda 4.1).
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { EventoESocial, Paginated } from "@/types";

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
