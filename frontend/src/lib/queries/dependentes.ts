/**
 * Hooks TanStack Query para Dependente (Bloco 1.3c).
 *
 * Endpoints:
 *   GET    /api/people/dependentes/?servidor=<id>   list filtrada
 *   GET    /api/people/dependentes/{id}/            detalhe
 *   POST   /api/people/dependentes/                 create
 *   PATCH  /api/people/dependentes/{id}/            update parcial
 *   DELETE /api/people/dependentes/{id}/            destroy
 *
 * Invalida também a queryKey de servidores (detalhe inclui dependentes embutidos).
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { DependenteDetail, DependenteWrite } from "@/types";

export type DependenteInput = Omit<DependenteWrite, "id">;

const BASE = "/people/dependentes/";

async function createDependente(payload: DependenteInput): Promise<DependenteDetail> {
  const { data } = await api.post<DependenteDetail>(BASE, payload);
  return data;
}

async function updateDependente(
  id: number,
  payload: Partial<DependenteInput>,
): Promise<DependenteDetail> {
  const { data } = await api.patch<DependenteDetail>(`${BASE}${id}/`, payload);
  return data;
}

async function deleteDependente(id: number): Promise<void> {
  await api.delete(`${BASE}${id}/`);
}

function invalidatePeople(qc: ReturnType<typeof useQueryClient>, tenant: string | null) {
  qc.invalidateQueries({ queryKey: ["servidores", tenant] });
  qc.invalidateQueries({ queryKey: ["dependentes", tenant] });
}

export function useCreateDependente() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createDependente,
    onSuccess: () => invalidatePeople(qc, activeTenant),
  });
}

export function useUpdateDependente() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: Partial<DependenteInput> }) =>
      updateDependente(id, payload),
    onSuccess: () => invalidatePeople(qc, activeTenant),
  });
}

export function useDeleteDependente() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deleteDependente,
    onSuccess: () => invalidatePeople(qc, activeTenant),
  });
}
