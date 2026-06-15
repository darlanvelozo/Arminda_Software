/**
 * Hooks TanStack Query para a programação de licença-prêmio (Onda 3.4).
 * Reusa useVinculosAtivos de ferias.ts para o seletor de servidores.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { LicencaPremioItem, Paginated } from "@/types";

export interface LicencaPremioItemInput {
  folha: number;
  vinculo: number;
  meses: number;
  dias: number;
}

const BASE = "/payroll/licenca-premio-itens/";
const key = (tenant: string | null, folhaId: number) =>
  ["lp-itens", tenant, folhaId] as const;

export function useLpItens(folhaId: number | null) {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: key(activeTenant, folhaId ?? 0),
    queryFn: async () => {
      const { data } = await api.get<Paginated<LicencaPremioItem>>(BASE, {
        params: { folha: folhaId, page_size: 500 },
      });
      return data;
    },
    enabled: !!activeTenant && folhaId !== null,
  });
}

export function useCreateLpItem(folhaId: number) {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: LicencaPremioItemInput) => {
      const { data } = await api.post<LicencaPremioItem>(BASE, payload);
      return data;
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: key(activeTenant, folhaId) }),
  });
}

export function useDeleteLpItem(folhaId: number) {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await api.delete(`${BASE}${id}/`);
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: key(activeTenant, folhaId) }),
  });
}
