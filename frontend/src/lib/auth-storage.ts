/**
 * Storage de tokens e tenant ativo (Bloco 1.3).
 *
 * - Tokens: localStorage. Trade-off conhecido vs cookie httpOnly:
 *   - Vantagem: simples, funciona offline, frontend tem controle total.
 *   - Desvantagem: vulnerável a XSS. Mitigação: Content-Security-Policy
 *     restritiva (a configurar no Bloco 6) + nada de innerHTML em código de
 *     domínio (já garantido por React).
 * - Tenant ativo: localStorage também — sobrevive a refresh de página.
 *
 * Chaves prefixadas com "arminda_" para não colidir com outras apps no mesmo
 * dominio em dev.
 */

const KEY_ACCESS = "arminda_access_token";
const KEY_REFRESH = "arminda_refresh_token";
const KEY_TENANT = "arminda_active_tenant";

function safeStorage(): Storage | null {
  if (typeof window === "undefined") return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function getAccessToken(): string | null {
  return safeStorage()?.getItem(KEY_ACCESS) ?? null;
}

export function setAccessToken(token: string): void {
  safeStorage()?.setItem(KEY_ACCESS, token);
}

export function getRefreshToken(): string | null {
  return safeStorage()?.getItem(KEY_REFRESH) ?? null;
}

export function setRefreshToken(token: string): void {
  safeStorage()?.setItem(KEY_REFRESH, token);
}

export function setTokens(access: string, refresh: string): void {
  setAccessToken(access);
  setRefreshToken(refresh);
}

export function clearTokens(): void {
  const s = safeStorage();
  s?.removeItem(KEY_ACCESS);
  s?.removeItem(KEY_REFRESH);
  s?.removeItem(KEY_TENANT);
}

export function getActiveTenantSchema(): string | null {
  return safeStorage()?.getItem(KEY_TENANT) ?? null;
}

export function setActiveTenantSchema(schema: string | null): void {
  const s = safeStorage();
  if (!s) return;
  if (schema) {
    s.setItem(KEY_TENANT, schema);
  } else {
    s.removeItem(KEY_TENANT);
  }
}
