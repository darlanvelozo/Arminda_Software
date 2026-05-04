/**
 * Hooks TanStack Query para gestão de usuários do município (Onda 1.5).
 *
 * Endpoints (tenant — exigem header X-Tenant):
 *   GET    /api/core/usuarios/          lista paginada
 *   POST   /api/core/usuarios/          cria User + papel (atômico)
 *   PATCH  /api/core/usuarios/{id}/     troca papel
 *   DELETE /api/core/usuarios/{id}/     remove papel (não deleta o User)
 *
 * Apenas admin_municipio + staff_arminda têm permissão.
 */

import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Paginated } from "@/types";

export interface UsuarioMunicipioPapel {
  id: number;
  usuario: {
    id: number;
    email: string;
    nome_completo: string;
    is_active: boolean;
    precisa_trocar_senha: boolean;
  };
  papel: string;
  criado_em: string;
}

export interface UsuarioCriacaoInput {
  email: string;
  nome_completo: string;
  papel: string;
  senha_temporaria?: string;
}

const BASE = "/core/usuarios/";

const usuariosKey = (tenant: string | null) => ["usuarios", tenant] as const;

async function fetchUsuarios(): Promise<Paginated<UsuarioMunicipioPapel>> {
  const { data } = await api.get<Paginated<UsuarioMunicipioPapel>>(BASE);
  return data;
}

async function createUsuario(payload: UsuarioCriacaoInput): Promise<UsuarioMunicipioPapel> {
  const { data } = await api.post<UsuarioMunicipioPapel>(BASE, payload);
  return data;
}

async function updatePapel(id: number, papel: string): Promise<UsuarioMunicipioPapel> {
  const { data } = await api.patch<UsuarioMunicipioPapel>(`${BASE}${id}/`, { papel });
  return data;
}

async function deletePapel(id: number): Promise<void> {
  await api.delete(`${BASE}${id}/`);
}

export function useUsuariosList() {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: [...usuariosKey(activeTenant), "list"],
    queryFn: fetchUsuarios,
    enabled: !!activeTenant,
    placeholderData: keepPreviousData,
  });
}

export function useCreateUsuario() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: createUsuario,
    onSuccess: () => qc.invalidateQueries({ queryKey: usuariosKey(activeTenant) }),
  });
}

export function useUpdatePapel() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, papel }: { id: number; papel: string }) => updatePapel(id, papel),
    onSuccess: () => qc.invalidateQueries({ queryKey: usuariosKey(activeTenant) }),
  });
}

export function useDeletePapel() {
  const { activeTenant } = useAuth();
  const qc = useQueryClient();
  return useMutation({
    mutationFn: deletePapel,
    onSuccess: () => qc.invalidateQueries({ queryKey: usuariosKey(activeTenant) }),
  });
}
