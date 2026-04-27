import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import HomePage from "@/pages/HomePage";

function renderWithProviders(ui: React.ReactNode) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>{ui}</MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("HomePage", () => {
  it("renderiza o título Arminda", () => {
    renderWithProviders(<HomePage />);
    expect(
      screen.getByRole("heading", { name: /arminda/i, level: 1 }),
    ).toBeInTheDocument();
  });

  it("mostra link para o repositório no GitHub", () => {
    renderWithProviders(<HomePage />);
    const link = screen.getByRole("link", { name: /repositório/i });
    expect(link).toHaveAttribute(
      "href",
      "https://github.com/darlanvelozo/Arminda_Software",
    );
  });
});
