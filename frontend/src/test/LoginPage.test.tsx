/**
 * Smoke do LoginPage (Bloco 1.3).
 *
 * Cobre:
 *   - render dos campos e botão
 *   - validação HTML5 de e-mail/senha required
 *   - submit chama login() do AuthContext (mock via vi.mock)
 *   - mensagem de erro aparece quando login falha
 */

import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";

import LoginPage from "@/pages/auth/LoginPage";
import { renderWithProviders } from "./utils";

const loginMock = vi.fn();

vi.mock("@/lib/auth-context", () => ({
  useAuth: () => ({
    isAuthenticated: false,
    isLoading: false,
    login: loginMock,
    user: null,
    activeTenant: null,
    papelAtual: null,
    logout: vi.fn(),
    switchTenant: vi.fn(),
    refresh: vi.fn(),
  }),
  AuthProvider: ({ children }: { children: React.ReactNode }) => children,
}));

describe("LoginPage", () => {
  beforeEach(() => loginMock.mockReset());
  afterEach(() => window.localStorage.clear());

  it("renderiza campos de e-mail, senha e botão", () => {
    renderWithProviders(<LoginPage />, { initialEntries: ["/login"] });
    expect(screen.getByLabelText(/e-mail/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/senha/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /entrar/i })).toBeInTheDocument();
  });

  it("submit chama login com email e senha", async () => {
    const user = userEvent.setup();
    loginMock.mockResolvedValueOnce({
      access: "a",
      refresh: "r",
      user: { municipios: [{ schema: "mun_x" }] },
    });
    renderWithProviders(<LoginPage />, { initialEntries: ["/login"] });

    await user.type(screen.getByLabelText(/e-mail/i), "ana@x.test");
    await user.type(screen.getByLabelText(/senha/i), "senha-segura-123");
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    expect(loginMock).toHaveBeenCalledOnce();
    expect(loginMock).toHaveBeenCalledWith({
      email: "ana@x.test",
      password: "senha-segura-123",
    });
  });

  it("mostra mensagem de erro quando login falha", async () => {
    const user = userEvent.setup();
    loginMock.mockRejectedValueOnce(new Error("oops"));
    renderWithProviders(<LoginPage />, { initialEntries: ["/login"] });

    await user.type(screen.getByLabelText(/e-mail/i), "x@y.test");
    await user.type(screen.getByLabelText(/senha/i), "qualquer-senha-12");
    await user.click(screen.getByRole("button", { name: /entrar/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/inv[aá]lid/i);
  });
});
