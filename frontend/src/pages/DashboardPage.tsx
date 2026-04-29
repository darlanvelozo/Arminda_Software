/**
 * DashboardPage — placeholder do Bloco 1.3.
 *
 * KPIs reais entram no Bloco 7 (BI). Por agora, apenas resumo do
 * município ativo + cards de navegação rápida.
 */

import { Briefcase, Building2, Coins, FileText, Users } from "lucide-react";
import { Link } from "react-router-dom";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";

const ATALHOS = [
  {
    label: "Servidores",
    descricao: "Cadastros, admissão, vínculos",
    to: "/servidores",
    icon: Users,
  },
  {
    label: "Cargos",
    descricao: "Cargos públicos do município",
    to: "/cargos",
    icon: Briefcase,
  },
  {
    label: "Lotações",
    descricao: "Secretarias e setores",
    to: "/lotacoes",
    icon: Building2,
  },
  {
    label: "Rubricas",
    descricao: "Proventos e descontos",
    to: "/rubricas",
    icon: Coins,
  },
  {
    label: "Relatórios",
    descricao: "Exportações e auditoria",
    to: "/relatorios",
    icon: FileText,
  },
];

export default function DashboardPage() {
  const { user, activeTenant } = useAuth();

  const municipio = user?.municipios.find((m) => m.schema === activeTenant);

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold tracking-tight">
          Bem-vindo, {user?.nome_completo || user?.email}
        </h1>
        {municipio ? (
          <p className="text-muted-foreground">
            {municipio.nome} · {municipio.uf} · {municipio.codigo_ibge}
          </p>
        ) : (
          <p className="text-muted-foreground">Nenhum município ativo.</p>
        )}
      </header>

      <section aria-labelledby="atalhos-heading" className="space-y-3">
        <h2 id="atalhos-heading" className="text-sm font-medium text-muted-foreground">
          Atalhos
        </h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {ATALHOS.map(({ label, descricao, to, icon: Icon }) => (
            <Link key={to} to={to} className="group">
              <Card className="h-full transition-colors group-hover:border-primary">
                <CardHeader>
                  <div className="flex items-center gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-md bg-primary/10 text-primary">
                      <Icon className="h-5 w-5" />
                    </span>
                    <div>
                      <CardTitle className="text-base">{label}</CardTitle>
                      <CardDescription className="text-xs">{descricao}</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="text-xs text-muted-foreground">
                  Em construção · Bloco 1.3b
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
