/**
 * Hooks TanStack Query para Vínculo Funcional + ações (Bloco 1.3c).
 *
 * Endpoints:
 *   GET    /api/people/vinculos/                    list (paginada)
 *   GET    /api/people/vinculos/{id}/               detalhe
 *   PATCH  /api/people/vinculos/{id}/               update parcial
 *   POST   /api/people/vinculos/{id}/transferir/    encerra + cria novo (atômico)
 *
 * Padrão: invalidamos a queryKey de servidores também — ao transferir um
 * vínculo, o detalhe do servidor (com vínculos embutidos) precisa atualizar.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { TransferenciaInput, VinculoDetail, VinculoWrite } from "@/types";

export type VinculoInput = Omit<VinculoWrite, "id">;

const BASE = "/people/vinculos/";

async function updateVinculo(id: number, payload: Partial<VinculoInput>): Promise<VinculoDetail> {
  const { data } = await api.patch<VinculoDetail>(`${BASE}${id}/`, payload);
  return data;
}

async function transferirVinculo(
  id: number,
  payload: TransferenciaInput,
): Promise<VinculoDetail> {
  const { data } = await api.post<VinculoDetail>(`${BASE}${id}/transferir/`, payload);
  return data;
}

export function useUpdateVinculo() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<VinculoInput> }) =>
      updateVinculo(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["servidores", activeTenant] });
      qc.invalidateQueries({ queryKey: ["vinculos", activeTenant] });
    },
  });
}

export function useTransferirVinculo() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: TransferenciaInput }) =>
      transferirVinculo(id, payload),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["servidores", activeTenant] });
      qc.invalidateQueries({ queryKey: ["vinculos", activeTenant] });
    },
  });
}
