/**
 * AppShell — layout raiz da área autenticada (Bloco 1.5).
 *
 * Estrutura:
 *   ┌──────────┬───────────────────────────┐
 *   │          │  Topbar (tenant + user)   │
 *   │ Sidebar  ├───────────────────────────┤
 *   │          │   <Outlet/>               │
 *   └──────────┴───────────────────────────┘
 *
 * Mantém o estado do CommandPalette (⌘K) e o atalho de teclado global.
 * Em < lg, a Sidebar fica escondida (mobile-first em onda futura).
 */

import { useCallback, useState } from "react";
import { Outlet } from "react-router-dom";

import { CommandPalette, useCommandPaletteShortcut } from "@/components/search/CommandPalette";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";

export function AppShell() {
  const [paletteOpen, setPaletteOpen] = useState(false);

  const openPalette = useCallback(() => setPaletteOpen(true), []);
  useCommandPaletteShortcut(openPalette);

  return (
    <div className="min-h-screen flex">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar onSearchOpen={openPalette} />
        <main className="flex-1 px-4 py-6 md:px-8 md:py-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
      <CommandPalette open={paletteOpen} onOpenChange={setPaletteOpen} />
    </div>
  );
}
