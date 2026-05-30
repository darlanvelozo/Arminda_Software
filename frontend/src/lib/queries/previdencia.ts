/**
 * Hooks TanStack Query para RegimePrevidenciario (RPPS) — Onda 2.4.
 *
 * Config do regime próprio do município (alíquotas, modo flat/progressivo,
 * vigência). Endpoint tenant: /api/payroll/regimes-previdenciarios/.
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Paginated, RegimePrevidenciario } from "@/types";

export type RegimePrevidenciarioInput = Omit<
  RegimePrevidenciario,
  "id" | "criado_em" | "atualizado_em" | "modo_contribuicao_display"
>;

const BASE = "/payroll/regimes-previdenciarios/";

const key = (tenant: string | null) => ["regimes-previdenciarios", tenant] as const;

async function fetchRegimes(): Promise<Paginated<RegimePrevidenciario>> {
  const { data } = await api.get<Paginated<RegimePrevidenciario>>(BASE, {
    params: { ordering: "-vigencia_inicio", page_size: 100 },
  });
  return data;
}

async function createRegime(
  payload: RegimePrevidenciarioInput,
): Promise<RegimePrevidenciario> {
  const { data } = await api.post<RegimePrevidenciario>(BASE, payload);
  return data;
}

async function updateRegime(
  id: number,
  payload: Partial<RegimePrevidenciarioInput>,
): Promise<RegimePrevidenciario> {
  const { data } = await api.patch<RegimePrevidenciario>(`${BASE}${id}/`, payload);
  return data;
}

async function deleteRegime(id: number): Promise<void> {
  await api.delete(`${BASE}${id}/`);
}

export function useRegimesPrevidenciarios() {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: [...key(activeTenant), "list"] as const,
    queryFn: fetchRegimes,
    enabled: !!activeTenant,
  });
}

export function useCreateRegimePrevidenciario() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createRegime,
    onSuccess: () => qc.invalidateQueries({ queryKey: key(activeTenant) }),
  });
}

export function useUpdateRegimePrevidenciario() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<RegimePrevidenciarioInput> }) =>
      updateRegime(id, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: key(activeTenant) }),
  });
}

export function useDeleteRegimePrevidenciario() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteRegime,
    onSuccess: () => qc.invalidateQueries({ queryKey: key(activeTenant) }),
  });
}
