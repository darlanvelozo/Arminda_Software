/**
 * <RequireAuth> wrapper (Bloco 1.3).
 *
 * Bloqueia o render dos filhos enquanto:
 *   - Auth está carregando (verificando /me/) → spinner
 *   - Não autenticado → redireciona para /login com state { from }
 */

import type { ReactElement } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useAuth } from "@/lib/auth-context";

export function RequireAuth({ children }: { children: ReactElement }) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="grid min-h-screen place-items-center" aria-live="polite">
        <span className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
