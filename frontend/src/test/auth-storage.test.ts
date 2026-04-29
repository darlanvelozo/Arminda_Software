/**
 * Testes do storage de tokens e tenant (Bloco 1.3).
 */

import { afterEach, beforeEach, describe, expect, it } from "vitest";

import {
  clearTokens,
  getAccessToken,
  getActiveTenantSchema,
  getRefreshToken,
  setAccessToken,
  setActiveTenantSchema,
  setTokens,
} from "@/lib/auth-storage";

describe("auth-storage", () => {
  beforeEach(() => window.localStorage.clear());
  afterEach(() => window.localStorage.clear());

  it("setTokens e getters retornam o que foi gravado", () => {
    setTokens("access-123", "refresh-456");
    expect(getAccessToken()).toBe("access-123");
    expect(getRefreshToken()).toBe("refresh-456");
  });

  it("setAccessToken sobrescreve só o access", () => {
    setTokens("a", "r");
    setAccessToken("a2");
    expect(getAccessToken()).toBe("a2");
    expect(getRefreshToken()).toBe("r");
  });

  it("clearTokens remove tudo (incluindo tenant)", () => {
    setTokens("a", "r");
    setActiveTenantSchema("mun_x");
    clearTokens();
    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
    expect(getActiveTenantSchema()).toBeNull();
  });

  it("setActiveTenantSchema(null) remove a chave", () => {
    setActiveTenantSchema("mun_y");
    expect(getActiveTenantSchema()).toBe("mun_y");
    setActiveTenantSchema(null);
    expect(getActiveTenantSchema()).toBeNull();
  });

  it("storage vazio retorna null sem erro", () => {
    expect(getAccessToken()).toBeNull();
    expect(getRefreshToken()).toBeNull();
    expect(getActiveTenantSchema()).toBeNull();
  });
});
