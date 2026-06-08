/**
 * Hooks TanStack Query para a programação de férias (FeriasItem) — Onda 3.3.
 *
 * Itens de uma folha de férias: /api/payroll/ferias-itens/?folha=
 * Seletor de vínculos ativos: /api/people/vinculos/?ativo=true
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { FeriasItem, Paginated, Vinculo } from "@/types";

export interface FeriasItemInput {
  folha: number;
  vinculo: number;
  dias_gozo: number;
  dias_abono: number;
  data_inicio?: string | null;
}

const BASE = "/payroll/ferias-itens/";
const key = (tenant: string | null, folhaId: number) =>
  ["ferias-itens", tenant, folhaId] as const;

export function useFeriasItens(folhaId: number | null) {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: key(activeTenant, folhaId ?? 0),
    queryFn: async () => {
      const { data } = await api.get<Paginated<FeriasItem>>(BASE, {
        params: { folha: folhaId, page_size: 500 },
      });
      return data;
    },
    enabled: !!activeTenant && folhaId !== null,
  });
}

export function useVinculosAtivos() {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: ["vinculos-ativos", activeTenant] as const,
    queryFn: async () => {
      const { data } = await api.get<Paginated<Vinculo>>("/people/vinculos/", {
        params: { ativo: true, page_size: 500, ordering: "servidor__nome" },
      });
      return data;
    },
    enabled: !!activeTenant,
  });
}

export function useCreateFeriasItem(folhaId: number) {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: FeriasItemInput) => {
      const { data } = await api.post<FeriasItem>(BASE, payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: key(activeTenant, folhaId) }),
  });
}

export function useDeleteFeriasItem(folhaId: number) {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`${BASE}${id}/`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: key(activeTenant, folhaId) }),
  });
}
