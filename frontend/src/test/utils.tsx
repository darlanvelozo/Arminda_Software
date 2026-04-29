/**
 * Helpers de teste (Bloco 1.3).
 *
 * Wrappers comuns:
 *   - renderWithProviders: QueryClient + MemoryRouter (sem auth)
 *   - renderWithAuth:      + AuthProvider (auth-context)
 *
 * Limpa localStorage entre testes para não contaminar.
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, type RenderOptions } from "@testing-library/react";
import type { ReactElement } from "react";
import { MemoryRouter } from "react-router-dom";

import { AuthProvider } from "@/lib/auth-context";

interface ProvidersOptions {
  initialEntries?: string[];
}

export function renderWithProviders(
  ui: ReactElement,
  { initialEntries = ["/"] }: ProvidersOptions = {},
  options?: RenderOptions,
) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={initialEntries}>{ui}</MemoryRouter>
    </QueryClientProvider>,
    options,
  );
}

export function renderWithAuth(
  ui: ReactElement,
  { initialEntries = ["/"] }: ProvidersOptions = {},
  options?: RenderOptions,
) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: 0 } },
  });
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={initialEntries}>
        <AuthProvider>{ui}</AuthProvider>
      </MemoryRouter>
    </QueryClientProvider>,
    options,
  );
}

export function clearLocalStorage(): void {
  if (typeof window !== "undefined") {
    window.localStorage.clear();
  }
}
