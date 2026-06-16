/**
 * Hooks TanStack Query para os lançamentos de folha complementar (Onda 3.5).
 * Reusa useVinculosAtivos de ferias.ts para o seletor de servidores e
 * useRubricasList de rubricas.ts para o seletor de rubricas.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { ComplementarItem, Paginated } from "@/types";

export interface ComplementarItemInput {
  folha: number;
  vinculo: number;
  rubrica: number;
  valor: string;
}

const BASE = "/payroll/complementar-itens/";
const key = (tenant: string | null, folhaId: number) =>
  ["complementar-itens", tenant, folhaId] as const;

export function useComplementarItens(folhaId: number | null) {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: key(activeTenant, folhaId ?? 0),
    queryFn: async () => {
      const { data } = await api.get<Paginated<ComplementarItem>>(BASE, {
        params: { folha: folhaId, page_size: 500 },
      });
      return data;
    },
    enabled: !!activeTenant && folhaId !== null,
  });
}

export function useCreateComplementarItem(folhaId: number) {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: ComplementarItemInput) => {
      const { data } = await api.post<ComplementarItem>(BASE, payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: key(activeTenant, folhaId) }),
  });
}

export function useDeleteComplementarItem(folhaId: number) {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`${BASE}${id}/`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: key(activeTenant, folhaId) }),
  });
}
