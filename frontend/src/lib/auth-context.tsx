/**
 * AuthContext + provider (Bloco 1.3).
 *
 * Uso:
 *   const { user, isAuthenticated, login, logout, switchTenant, activeTenant } = useAuth();
 *
 * Estado:
 *   - user: dados do `/api/auth/me/`. null se nao autenticado.
 *   - activeTenant: schema do municipio selecionado no Topbar.
 *
 * Persistencia:
 *   - Tokens em localStorage (auth-storage.ts).
 *   - Tenant ativo em localStorage.
 *   - Ao montar, tenta /auth/me/ se houver token — se 401, limpa tudo.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import { useQueryClient } from "@tanstack/react-query";

import { fetchMe, login as authLogin, logout as authLogout } from "@/lib/auth";
import {
  clearTokens,
  getAccessToken,
  getActiveTenantSchema,
  setActiveTenantSchema,
} from "@/lib/auth-storage";
import type { LoginRequest, LoginResponse, PapelEmMunicipio, UserMe } from "@/types";

interface AuthContextValue {
  user: UserMe | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  activeTenant: string | null;
  papelAtual: string | null;
  login: (payload: LoginRequest) => Promise<LoginResponse>;
  logout: () => Promise<void>;
  switchTenant: (schema: string) => void;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState<UserMe | null>(null);
  const [activeTenant, setActiveTenant] = useState<string | null>(getActiveTenantSchema());
  const [isLoading, setIsLoading] = useState(true);

  const hydrate = useCallback(async () => {
    if (!getAccessToken()) {
      setIsLoading(false);
      return;
    }
    try {
      const me = await fetchMe();
      setUser(me);
      // Se ainda não escolheu tenant e tem 1 só, ativa
      if (!getActiveTenantSchema() && me.municipios.length === 1) {
        const schema = me.municipios[0].schema;
        setActiveTenantSchema(schema);
        setActiveTenant(schema);
      }
    } catch {
      clearTokens();
      setUser(null);
      setActiveTenant(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void hydrate();
  }, [hydrate]);

  const handleLogin = useCallback(
    async (payload: LoginRequest) => {
      const data = await authLogin(payload);
      setUser(data.user);
      const ativo = getActiveTenantSchema();
      setActiveTenant(ativo);
      // Limpa cache de queries para evitar dados de outro usuário
      await queryClient.invalidateQueries();
      return data;
    },
    [queryClient],
  );

  const handleLogout = useCallback(async () => {
    await authLogout();
    setUser(null);
    setActiveTenant(null);
    queryClient.clear();
  }, [queryClient]);

  const switchTenant = useCallback(
    (schema: string) => {
      setActiveTenantSchema(schema);
      setActiveTenant(schema);
      // Trocar de tenant invalida todo cache de dados (que era do outro tenant)
      queryClient.clear();
    },
    [queryClient],
  );

  const papelAtual = useMemo(() => {
    if (!user || !activeTenant) return null;
    const m: PapelEmMunicipio | undefined = user.municipios.find((m) => m.schema === activeTenant);
    return m?.papel ?? null;
  }, [user, activeTenant]);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      activeTenant,
      papelAtual,
      login: handleLogin,
      logout: handleLogout,
      switchTenant,
      refresh: hydrate,
    }),
    [user, isLoading, activeTenant, papelAtual, handleLogin, handleLogout, switchTenant, hydrate],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth deve ser usado dentro de <AuthProvider>");
  }
  return ctx;
}
