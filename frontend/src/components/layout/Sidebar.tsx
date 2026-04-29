/**
 * Sidebar — Bloco 1.3 (design Arminda).
 *
 * Estrutura:
 *   - Header com Logo (collapsable: vira só ícone).
 *   - Município context card (mostra ativo + atalho para troca).
 *   - Nav principal agrupada com label "OPERAÇÃO".
 *   - Footer: Configurações + botão de colapso.
 *
 * Larguras: 248px expandido, 64px colapsado.
 */

import {
  Briefcase,
  Building2,
  ChevronRight,
  FileText,
  Home,
  Library,
  PanelLeft,
  RefreshCw,
  Settings,
  Tag,
  Users,
  Wallet,
} from "lucide-react";
import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";

import { Logo } from "@/components/brand/Logo";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";

interface ItemNav {
  label: string;
  to: string;
  icon: typeof Home;
}

const ITENS: ItemNav[] = [
  { label: "Dashboard", to: "/", icon: Home },
  { label: "Servidores", to: "/servidores", icon: Users },
  { label: "Cargos", to: "/cargos", icon: Briefcase },
  { label: "Lotações", to: "/lotacoes", icon: Library },
  { label: "Folha", to: "/folha", icon: Wallet },
  { label: "Rubricas", to: "/rubricas", icon: Tag },
  { label: "Relatórios", to: "/relatorios", icon: FileText },
];

export function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);
  const { user, activeTenant } = useAuth();
  const navigate = useNavigate();
  const municipio = user?.municipios.find((m) => m.schema === activeTenant);

  const width = collapsed ? 64 : 248;

  return (
    <aside
      className="hidden lg:flex flex-col flex-shrink-0 border-r bg-card transition-[width] duration-200"
      style={{ width }}
    >
      {/* Header */}
      <div
        className="h-[60px] border-b flex items-center"
        style={{ padding: collapsed ? "0 12px" : "0 16px" }}
      >
        {collapsed ? <Logo withText={false} /> : <Logo />}
      </div>

      {/* Município context card */}
      {!collapsed && (
        <div className="p-3">
          <div className="flex items-center gap-2.5 rounded-md bg-muted p-2.5">
            <span className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground flex-shrink-0">
              <Building2 className="h-4 w-4" />
            </span>
            <div className="flex-1 min-w-0">
              <div className="text-[11px] uppercase tracking-wider font-medium text-muted-foreground">
                Município
              </div>
              <div className="text-sm font-medium truncate">
                {municipio ? `${municipio.nome} · ${municipio.uf}` : "Sem município ativo"}
              </div>
            </div>
            {(user?.municipios.length ?? 0) > 1 && (
              <button
                onClick={() => navigate("/selecionar-municipio")}
                className="p-1.5 rounded-sm text-muted-foreground hover:text-foreground hover:bg-accent transition-colors"
                aria-label="Trocar município"
                title="Trocar município"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </button>
            )}
          </div>
        </div>
      )}

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto" style={{ padding: collapsed ? 8 : 12 }}>
        {!collapsed && (
          <div className="text-[11px] uppercase tracking-wider font-medium text-muted-foreground mb-2 px-3">
            Operação
          </div>
        )}
        <div className="flex flex-col gap-0.5">
          {ITENS.map(({ label, to, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              title={collapsed ? label : undefined}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-md text-sm font-medium transition-colors",
                  collapsed ? "h-10 w-10 justify-center" : "h-9 px-3",
                  isActive
                    ? "bg-primary-soft text-primary-soft-foreground [&_svg]:text-primary"
                    : "text-muted-foreground hover:bg-accent hover:text-foreground",
                )
              }
            >
              <Icon className="h-4 w-4 shrink-0" />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </div>
      </nav>

      {/* Footer */}
      <div className="border-t" style={{ padding: collapsed ? 8 : 12 }}>
        <div className="flex flex-col gap-0.5">
          <button
            type="button"
            onClick={() => navigate("/configuracoes")}
            className={cn(
              "flex items-center gap-2.5 rounded-md text-sm font-medium text-muted-foreground hover:bg-accent hover:text-foreground transition-colors",
              collapsed ? "h-10 w-10 justify-center" : "h-9 px-3",
            )}
            title={collapsed ? "Configurações" : undefined}
          >
            <Settings className="h-4 w-4 shrink-0" />
            {!collapsed && <span>Configurações</span>}
          </button>
          <button
            type="button"
            onClick={() => setCollapsed((c) => !c)}
            className={cn(
              "flex items-center gap-2.5 rounded-md text-sm font-medium text-muted-foreground hover:bg-accent hover:text-foreground transition-colors",
              collapsed ? "h-10 w-10 justify-center" : "h-9 px-3",
            )}
            title={collapsed ? "Expandir" : "Colapsar"}
            aria-label={collapsed ? "Expandir sidebar" : "Colapsar sidebar"}
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4 shrink-0" />
            ) : (
              <PanelLeft className="h-4 w-4 shrink-0" />
            )}
            {!collapsed && <span>Colapsar</span>}
          </button>
        </div>
      </div>
    </aside>
  );
}
