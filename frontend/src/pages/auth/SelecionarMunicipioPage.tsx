/**
 * SelecionarMunicipioPage (Bloco 1.3).
 *
 * Mostrada após login quando o usuário tem 2+ municípios. Após escolher,
 * redireciona para /. Também pode ser acessada via dropdown do Topbar.
 */

import { Building2 } from "lucide-react";
import { Navigate, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";

const PAPEL_LABEL: Record<string, string> = {
  staff_arminda: "Staff Arminda",
  admin_municipio: "Administrador",
  rh_municipio: "RH",
  financeiro_municipio: "Financeiro",
  leitura_municipio: "Leitura",
};

export default function SelecionarMunicipioPage() {
  const { user, switchTenant } = useAuth();
  const navigate = useNavigate();

  if (!user) return <Navigate to="/login" replace />;
  if (user.municipios.length === 0) {
    // Caso típico de staff_arminda: vai pro dashboard mesmo
    return <Navigate to="/" replace />;
  }

  return (
    <main className="min-h-screen grid place-items-center bg-muted/30 px-4 py-10">
      <div className="w-full max-w-md space-y-6">
        <header className="text-center space-y-1">
          <h1 className="text-2xl font-bold tracking-tight">Selecionar município</h1>
          <p className="text-sm text-muted-foreground">
            Você opera em mais de um município. Escolha qual acessar agora.
          </p>
        </header>

        <ul className="space-y-3">
          {user.municipios.map((m) => (
            <li key={m.schema}>
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex items-center gap-3">
                    <span className="flex h-9 w-9 items-center justify-center rounded-md bg-primary/10 text-primary">
                      <Building2 className="h-5 w-5" />
                    </span>
                    <div>
                      <CardTitle className="text-base">
                        {m.nome} · {m.uf}
                      </CardTitle>
                      <p className="text-xs text-muted-foreground">
                        IBGE {m.codigo_ibge} · {PAPEL_LABEL[m.papel] ?? m.papel}
                      </p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <Button
                    type="button"
                    onClick={() => {
                      switchTenant(m.schema);
                      navigate("/");
                    }}
                    className="w-full"
                  >
                    Acessar
                  </Button>
                </CardContent>
              </Card>
            </li>
          ))}
        </ul>
      </div>
    </main>
  );
}
