/**
 * Sidebar de navegação (Bloco 1.3).
 *
 * Itens estáticos por agora. Permissões finas (esconder Rubrica para RH,
 * etc.) entram quando aparecer caso de uso real — Bloco 1.5+.
 */

import { Briefcase, Building2, Coins, FileText, LayoutDashboard, Users } from "lucide-react";
import { NavLink } from "react-router-dom";

import { cn } from "@/lib/utils";

interface ItemNav {
  label: string;
  to: string;
  icon: typeof LayoutDashboard;
}

const ITENS: ItemNav[] = [
  { label: "Dashboard", to: "/", icon: LayoutDashboard },
  { label: "Servidores", to: "/servidores", icon: Users },
  { label: "Cargos", to: "/cargos", icon: Briefcase },
  { label: "Lotações", to: "/lotacoes", icon: Building2 },
  { label: "Rubricas", to: "/rubricas", icon: Coins },
  { label: "Relatórios", to: "/relatorios", icon: FileText },
];

export function Sidebar() {
  return (
    <aside className="hidden lg:flex w-60 shrink-0 flex-col border-r bg-card">
      <div className="px-6 py-5 border-b">
        <span className="text-xl font-bold tracking-tight text-primary">Arminda</span>
      </div>
      <nav className="flex-1 px-3 py-4 space-y-1">
        {ITENS.map(({ label, to, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground",
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
