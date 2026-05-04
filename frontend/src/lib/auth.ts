/**
 * Funções de autenticação (Bloco 1.3).
 *
 * Camada fina entre `api.ts` (axios) e o `AuthContext` (estado React).
 * Não tem estado próprio — apenas chama o backend e atualiza storage.
 */

import { api } from "@/lib/api";
import { clearTokens, getRefreshToken, setActiveTenantSchema, setTokens } from "@/lib/auth-storage";
import type { LoginRequest, LoginResponse, UserMe } from "@/types";

export async function login(payload: LoginRequest): Promise<LoginResponse> {
  const { data } = await api.post<LoginResponse>("/auth/login/", payload);
  setTokens(data.access, data.refresh);
  // Se o usuário só tem 1 município, já seta como ativo
  if (data.user.municipios.length === 1) {
    setActiveTenantSchema(data.user.municipios[0].schema);
  }
  return data;
}

export async function logout(): Promise<void> {
  const refresh = getRefreshToken();
  if (refresh) {
    try {
      await api.post("/auth/logout/", { refresh });
    } catch {
      // Logout local mesmo se o blacklist falhar (ex: token já expirado)
    }
  }
  clearTokens();
}

export async function fetchMe(): Promise<UserMe> {
  const { data } = await api.get<UserMe>("/auth/me/");
  return data;
}

export async function updateMe(payload: { nome_completo: string }): Promise<UserMe> {
  const { data } = await api.patch<UserMe>("/auth/me/", payload);
  return data;
}

export interface ChangePasswordPayload {
  current_password: string;
  new_password: string;
  new_password_confirm: string;
}

export async function changePassword(payload: ChangePasswordPayload): Promise<void> {
  await api.post("/auth/change-password/", payload);
}
