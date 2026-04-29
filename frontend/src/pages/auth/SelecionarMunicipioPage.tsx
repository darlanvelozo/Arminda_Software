/**
 * SelecionarMunicipioPage — Bloco 1.3 (design Arminda).
 *
 * Mostrada após login quando o usuário tem 2+ municípios.
 * Cards radio-style: clicar seleciona, botão confirma.
 */

import { ArrowLeft, ArrowRight, Building2 } from "lucide-react";
import { useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";

import { Logo } from "@/components/brand/Logo";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth-context";
import { cn } from "@/lib/utils";

const PAPEL_LABEL: Record<string, string> = {
  staff_arminda: "Staff Arminda",
  admin_municipio: "Administrador",
  rh_municipio: "RH",
  financeiro_municipio: "Financeiro",
  leitura_municipio: "Leitura",
};

export default function SelecionarMunicipioPage() {
  const { user, activeTenant, switchTenant, logout } = useAuth();
  const navigate = useNavigate();
  const [selected, setSelected] = useState<string | null>(
    activeTenant ?? user?.municipios[0]?.schema ?? null,
  );

  if (!user) return <Navigate to="/login" replace />;
  if (user.municipios.length === 0) return <Navigate to="/" replace />;

  function handleConfirm() {
    if (!selected) return;
    switchTenant(selected);
    navigate("/");
  }

  async function handleVoltar() {
    await logout();
    navigate("/login");
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-10">
      <div className="w-full max-w-md space-y-7">
        <div className="text-center space-y-3">
          <Logo />
          <button
            type="button"
            onClick={handleVoltar}
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground"
          >
            <ArrowLeft className="h-3 w-3" /> Trocar de conta
          </button>
        </div>

        <header className="text-center space-y-1">
          <h1 className="font-semibold" style={{ fontSize: 22, letterSpacing: "-0.015em" }}>
            Selecione o município
          </h1>
          <p className="text-sm text-muted-foreground">
            Sua conta tem acesso a {user.municipios.length} prefeituras.
          </p>
        </header>

        <div role="radiogroup" className="space-y-2.5">
          {user.municipios.map((m) => {
            const isSelected = selected === m.schema;
            return (
              <button
                key={m.schema}
                type="button"
                role="radio"
                aria-checked={isSelected}
                onClick={() => setSelected(m.schema)}
                className={cn(
                  "w-full flex items-center gap-3 rounded-md border bg-card p-3.5 text-left transition-colors",
                  isSelected ? "border-primary bg-primary-soft" : "hover:bg-accent",
                )}
              >
                <span
                  className={cn(
                    "flex h-9 w-9 items-center justify-center rounded-md flex-shrink-0",
                    isSelected
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted text-muted-foreground",
                  )}
                >
                  <Building2 className="h-4.5 w-4.5" />
                </span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium truncate">
                    Prefeitura de {m.nome} · {m.uf}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    IBGE {m.codigo_ibge} · {PAPEL_LABEL[m.papel] ?? m.papel}
                  </div>
                </div>
                <span
                  className={cn(
                    "h-4 w-4 rounded-full border-2 inline-flex items-center justify-center flex-shrink-0",
                    isSelected ? "border-primary" : "border-border-strong",
                  )}
                >
                  {isSelected && <span className="h-2 w-2 rounded-full bg-primary" />}
                </span>
              </button>
            );
          })}
        </div>

        <Button type="button" onClick={handleConfirm} disabled={!selected} className="w-full">
          Acessar Arminda
          <ArrowRight className="h-4 w-4 ml-1" />
        </Button>
      </div>
    </div>
  );
}
