/**
 * Cliente axios do Arminda (Bloco 1.3).
 *
 * Responsabilidades:
 * - Anexar `Authorization: Bearer <access>` em toda request autenticada.
 * - Anexar `X-Tenant: <schema>` quando há tenant ativo (escolhido no Topbar).
 * - Em 401: tentar refresh; se falhar, limpar storage e redirecionar para login.
 *
 * As chamadas saem do cliente único `api`. Hooks de domínio usam-no via
 * TanStack Query — nunca usar `fetch` ou outra instância de axios.
 */

import axios, { AxiosError, type AxiosRequestConfig, type InternalAxiosRequestConfig } from "axios";

import {
  clearTokens,
  getAccessToken,
  getActiveTenantSchema,
  getRefreshToken,
  setAccessToken,
} from "@/lib/auth-storage";

const API_URL = import.meta.env.VITE_API_URL || "/api";

export const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
  // 30s — endpoints de cálculo de folha podem demorar
  timeout: 30_000,
});

// ============================================================
// Request interceptor: anexa JWT + X-Tenant
// ============================================================

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.set("Authorization", `Bearer ${token}`);
  }
  const tenant = getActiveTenantSchema();
  if (tenant) {
    config.headers.set("X-Tenant", tenant);
  }
  return config;
});

// ============================================================
// Response interceptor: refresh em 401, redirect em falha
// ============================================================

interface RetriableConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

let refreshInflight: Promise<string | null> | null = null;

async function tryRefresh(): Promise<string | null> {
  if (refreshInflight) return refreshInflight;

  const refresh = getRefreshToken();
  if (!refresh) return null;

  refreshInflight = (async () => {
    try {
      const response = await axios.post(`${API_URL}/auth/refresh/`, {
        refresh,
      });
      const newAccess = response.data.access as string;
      setAccessToken(newAccess);
      return newAccess;
    } catch {
      return null;
    } finally {
      refreshInflight = null;
    }
  })();

  return refreshInflight;
}

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as RetriableConfig | undefined;

    // Não tenta refresh em endpoints de auth (evita loop infinito)
    const isAuthEndpoint = original?.url?.includes("/auth/");

    if (error.response?.status === 401 && original && !original._retry && !isAuthEndpoint) {
      original._retry = true;
      const newAccess = await tryRefresh();
      if (newAccess) {
        original.headers?.set?.("Authorization", `Bearer ${newAccess}`);
        return api.request(original);
      }
      // refresh falhou → desloga e redireciona
      clearTokens();
      if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
        window.location.assign("/login");
      }
    }

    return Promise.reject(error);
  },
);

// ============================================================
// Helpers
// ============================================================

/**
 * Helper para extrair `code` de erro de domínio do backend.
 * Backend retorna { detail, code } em ValidationError.
 */
export function extractDomainErrorCode(error: unknown): string | null {
  if (error instanceof AxiosError && error.response?.data) {
    const data = error.response.data as Record<string, unknown>;
    if (typeof data.code === "string") return data.code;
  }
  return null;
}

export function extractDomainErrorMessage(error: unknown): string | null {
  if (error instanceof AxiosError && error.response?.data) {
    const data = error.response.data as Record<string, unknown>;
    if (typeof data.detail === "string") return data.detail;
  }
  return null;
}

export type { AxiosRequestConfig };
