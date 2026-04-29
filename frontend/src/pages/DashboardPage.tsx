/**
 * DashboardPage — Bloco 1.3 (design Arminda).
 *
 * Por agora, header com saudação + município ativo + cards-KPI placeholder
 * + grid de atalhos. KPIs reais entram no Bloco 7 (BI).
 */

import {
  ArrowRight,
  Briefcase,
  Building2,
  Coins,
  FileText,
  Library,
  Tag,
  TrendingUp,
  Users,
  Wallet,
} from "lucide-react";
import { Link } from "react-router-dom";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";

const ATALHOS = [
  {
    label: "Servidores",
    descricao: "Cadastro, admissão, vínculos",
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
    icon: Library,
  },
  {
    label: "Folha",
    descricao: "Competências e fechamento",
    to: "/folha",
    icon: Wallet,
  },
  {
    label: "Rubricas",
    descricao: "Proventos e descontos",
    to: "/rubricas",
    icon: Tag,
  },
  {
    label: "Relatórios",
    descricao: "eSocial, RAIS, DIRF",
    to: "/relatorios",
    icon: FileText,
  },
];

const KPI_PLACEHOLDER = [
  { label: "Servidores ativos", valor: "—", hint: "em breve", icon: Users },
  { label: "Folha mensal", valor: "—", hint: "Bloco 2", icon: Coins },
  { label: "Variação 30d", valor: "—", hint: "Bloco 7", icon: TrendingUp },
];

export default function DashboardPage() {
  const { user, activeTenant } = useAuth();
  const municipio = user?.municipios.find((m) => m.schema === activeTenant);
  const display = user?.nome_completo || user?.email || "";

  return (
    <div className="space-y-8">
      <header className="space-y-1">
        <h1 className="font-semibold" style={{ fontSize: 28, letterSpacing: "-0.015em" }}>
          Olá, {display.split(" ")[0] || display}
        </h1>
        <p className="text-sm text-muted-foreground inline-flex items-center gap-1.5">
          <Building2 className="h-4 w-4" />
          {municipio
            ? `${municipio.nome} · ${municipio.uf} · IBGE ${municipio.codigo_ibge}`
            : "Sem município ativo"}
        </p>
      </header>

      {/* KPIs placeholder */}
      <section aria-labelledby="kpi-heading" className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <h2 id="kpi-heading" className="sr-only">
          Indicadores
        </h2>
        {KPI_PLACEHOLDER.map(({ label, valor, hint, icon: Icon }) => (
          <Card key={label} className="border-border">
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardDescription className="text-xs uppercase tracking-wider font-medium">
                  {label}
                </CardDescription>
                <Icon className="h-4 w-4 text-muted-foreground" />
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <div
                className="font-semibold tabular-nums"
                style={{ fontSize: 22, letterSpacing: "-0.015em" }}
              >
                {valor}
              </div>
              <p className="text-xs text-muted-foreground mt-1">{hint}</p>
            </CardContent>
          </Card>
        ))}
      </section>

      {/* Atalhos */}
      <section aria-labelledby="atalhos-heading" className="space-y-3">
        <h2
          id="atalhos-heading"
          className="text-[11px] uppercase tracking-wider font-medium text-muted-foreground"
        >
          Atalhos
        </h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {ATALHOS.map(({ label, descricao, to, icon: Icon }) => (
            <Link key={to} to={to} className="group">
              <Card className="h-full transition-colors group-hover:border-primary group-hover:shadow-sm">
                <CardHeader className="space-y-3">
                  <span className="inline-flex h-10 w-10 items-center justify-center rounded-md bg-primary-soft text-primary-soft-foreground">
                    <Icon className="h-5 w-5" />
                  </span>
                  <div className="space-y-1">
                    <CardTitle className="text-base">{label}</CardTitle>
                    <CardDescription className="text-xs">{descricao}</CardDescription>
                  </div>
                </CardHeader>
                <CardContent className="text-xs text-muted-foreground inline-flex items-center gap-1">
                  Acessar <ArrowRight className="h-3 w-3" />
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
