/**
 * AppShell — layout raiz da área autenticada (Bloco 1.3).
 *
 * Estrutura:
 *   ┌──────────┬───────────────────────────┐
 *   │          │  Topbar (tenant + user)   │
 *   │ Sidebar  ├───────────────────────────┤
 *   │          │   <Outlet/>               │
 *   └──────────┴───────────────────────────┘
 *
 * Em < lg, a Sidebar fica escondida (mobile-first virá no Bloco 1.5).
 */

import { Outlet } from "react-router-dom";

import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";

export function AppShell() {
  return (
    <div className="min-h-screen flex">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Topbar />
        <main className="flex-1 px-4 py-6 md:px-8 md:py-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
