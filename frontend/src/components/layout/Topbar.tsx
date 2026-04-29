/**
 * Topbar — Bloco 1.3 (design Arminda).
 *
 * Estrutura:
 *   - Esquerda: breadcrumb (gerado automaticamente da rota).
 *   - Centro/direita: search trigger (placeholder do CmdK — Onda 1.3b).
 *   - Direita: separador, toggle de tema, sino (placeholder), avatar dropdown.
 *
 * Altura fixa: 60px.
 */

import { Bell, ChevronRight, Moon, Search, Sun } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
import { useAuth } from "@/lib/auth-context";
import { useTheme } from "@/lib/theme";

const PAPEL_LABEL: Record<string, string> = {
  staff_arminda: "Staff Arminda",
  admin_municipio: "Administrador",
  rh_municipio: "RH",
  financeiro_municipio: "Financeiro",
  leitura_municipio: "Leitura",
};

const SECTION_LABELS: Record<string, string> = {
  "": "Dashboard",
  servidores: "Servidores",
  cargos: "Cargos",
  lotacoes: "Lotações",
  folha: "Folha",
  rubricas: "Rubricas",
  relatorios: "Relatórios",
  configuracoes: "Configurações",
  "selecionar-municipio": "Selecionar município",
};

function inicial(nome: string): string {
  const n = nome.trim();
  return n ? n[0].toUpperCase() : "?";
}

function Breadcrumb() {
  const location = useLocation();
  const segments = location.pathname.split("/").filter(Boolean);
  if (segments.length === 0) {
    return <span className="text-sm font-medium">{SECTION_LABELS[""]}</span>;
  }
  return (
    <nav className="flex items-center gap-1.5 text-sm" aria-label="breadcrumb">
      <Link to="/" className="text-muted-foreground hover:text-foreground">
        {SECTION_LABELS[""]}
      </Link>
      {segments.map((seg, i) => {
        const last = i === segments.length - 1;
        const label = SECTION_LABELS[seg] ?? seg;
        return (
          <span key={i} className="flex items-center gap-1.5">
            <ChevronRight className="h-3 w-3 text-muted-foreground" />
            <span className={last ? "font-medium text-foreground" : "text-muted-foreground"}>
              {label}
            </span>
          </span>
        );
      })}
    </nav>
  );
}

function SearchTrigger() {
  return (
    <button
      type="button"
      className="hidden md:flex items-center gap-2 h-9 px-3 rounded-md border bg-muted text-muted-foreground text-[13px] min-w-[280px] hover:bg-accent transition-colors"
      title="Buscar (placeholder — Onda 1.3b vai implementar CmdK)"
      aria-label="Buscar"
    >
      <Search className="h-3.5 w-3.5" />
      <span>Buscar servidor, cargo, rubrica…</span>
      <kbd className="ml-auto font-mono text-[11px] px-1.5 py-0.5 bg-background border rounded-sm">
        ⌘K
      </kbd>
    </button>
  );
}

function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      onClick={toggleTheme}
      aria-label={theme === "dark" ? "Tema claro" : "Tema escuro"}
      title={theme === "dark" ? "Tema claro" : "Tema escuro"}
    >
      {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </Button>
  );
}

function NotifTrigger() {
  return (
    <Button
      type="button"
      variant="ghost"
      size="icon"
      className="relative"
      aria-label="Notificações"
      title="Notificações (em breve)"
    >
      <Bell className="h-4 w-4" />
      <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-destructive ring-2 ring-card" />
    </Button>
  );
}

function PerfilDropdown() {
  const { user, logout, papelAtual } = useAuth();
  const navigate = useNavigate();
  if (!user) return null;
  const display = user.nome_completo || user.email;

  async function handleLogout() {
    await logout();
    navigate("/login");
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          className="flex items-center gap-2 rounded-full p-1 hover:bg-accent transition-colors"
        >
          <Avatar className="h-7 w-7">
            <AvatarFallback className="text-xs bg-secondary">{inicial(display)}</AvatarFallback>
          </Avatar>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>
          <div className="flex flex-col">
            <span className="text-sm font-medium">{display}</span>
            <span className="text-xs text-muted-foreground">{user.email}</span>
            {papelAtual && (
              <span className="mt-1.5 inline-flex items-center gap-1.5 rounded-full bg-primary-soft px-2 py-0.5 text-[11px] font-medium text-primary-soft-foreground w-fit">
                {PAPEL_LABEL[papelAtual] ?? papelAtual}
              </span>
            )}
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem disabled>Meu perfil</DropdownMenuItem>
        <DropdownMenuItem disabled>Trocar senha</DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          onSelect={handleLogout}
          className="text-destructive focus:text-destructive"
        >
          Sair
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function Topbar() {
  return (
    <header className="h-[60px] flex-shrink-0 border-b bg-card flex items-center px-6 gap-4">
      <div className="flex-1 min-w-0">
        <Breadcrumb />
      </div>

      <SearchTrigger />

      <Separator orientation="vertical" className="h-6 hidden md:block" />

      <ThemeToggle />
      <NotifTrigger />
      <PerfilDropdown />
    </header>
  );
}
