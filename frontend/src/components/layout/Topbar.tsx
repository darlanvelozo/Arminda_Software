/**
 * Topbar (Bloco 1.3).
 *
 * Conteudo:
 *   - Nome do município ativo (clicável: troca de município se houver >1)
 *   - Avatar + dropdown do usuário (logout)
 *
 * Troca de município:
 *   - Se user tem só 1 município, dropdown não aparece (label estático).
 *   - Trocar invalida cache do TanStack Query (handled by AuthContext).
 */

import { ChevronDown, LogOut, User } from "lucide-react";
import { useNavigate } from "react-router-dom";

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
import { useAuth } from "@/lib/auth-context";
import type { PapelEmMunicipio } from "@/types";

const PAPEL_LABEL: Record<string, string> = {
  staff_arminda: "Staff Arminda",
  admin_municipio: "Administrador",
  rh_municipio: "RH",
  financeiro_municipio: "Financeiro",
  leitura_municipio: "Leitura",
};

function inicial(nome: string): string {
  const n = nome.trim();
  if (!n) return "?";
  return n[0].toUpperCase();
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
        <Button variant="ghost" className="gap-2 h-9 px-2">
          <Avatar className="h-7 w-7">
            <AvatarFallback className="text-xs">{inicial(display)}</AvatarFallback>
          </Avatar>
          <span className="hidden md:inline text-sm font-medium">{display}</span>
          <ChevronDown className="h-4 w-4 opacity-60" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>
          <div className="flex flex-col">
            <span className="text-sm">{display}</span>
            <span className="text-xs text-muted-foreground">{user.email}</span>
            {papelAtual && (
              <span className="text-xs text-muted-foreground mt-1">
                Papel: {PAPEL_LABEL[papelAtual] ?? papelAtual}
              </span>
            )}
          </div>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem disabled>
          <User className="h-4 w-4 mr-2" />
          Meu perfil
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={handleLogout}>
          <LogOut className="h-4 w-4 mr-2" />
          Sair
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

function TenantSwitcher() {
  const { user, activeTenant, switchTenant } = useAuth();
  if (!user || user.municipios.length === 0) {
    return <span className="text-sm text-muted-foreground">Sem município vinculado</span>;
  }

  const ativo: PapelEmMunicipio | undefined = user.municipios.find(
    (m) => m.schema === activeTenant,
  );

  if (user.municipios.length === 1) {
    const m = user.municipios[0];
    return (
      <div className="text-sm">
        <span className="font-medium">{m.nome}</span>
        <span className="text-muted-foreground"> · {m.uf}</span>
      </div>
    );
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <span className="font-medium">
            {ativo ? `${ativo.nome} · ${ativo.uf}` : "Selecionar município"}
          </span>
          <ChevronDown className="h-4 w-4 opacity-60" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="w-64">
        <DropdownMenuLabel>Trocar de município</DropdownMenuLabel>
        <DropdownMenuSeparator />
        {user.municipios.map((m) => (
          <DropdownMenuItem
            key={m.schema}
            onSelect={() => switchTenant(m.schema)}
            className="flex flex-col items-start gap-0.5"
          >
            <span className="text-sm font-medium">
              {m.nome} · {m.uf}
            </span>
            <span className="text-xs text-muted-foreground">{PAPEL_LABEL[m.papel] ?? m.papel}</span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function Topbar() {
  return (
    <header className="h-14 border-b bg-card flex items-center justify-between px-4 md:px-6">
      <TenantSwitcher />
      <PerfilDropdown />
    </header>
  );
}
