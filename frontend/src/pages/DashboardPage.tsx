/**
 * DashboardPage — Bloco 1.5b (organização por vínculo e natureza).
 *
 * Estrutura:
 *   - Header com saudação + município ativo + total de servidores ativos
 *   - Seção "Por vínculo": Efetivos, Comissionados, Contratados, Eletivos —
 *     cada card navega para /servidores?regime=X
 *   - Seção "Por área": Administração, Saúde, Educação, Assistência social —
 *     cada card navega para /servidores?natureza=Y
 *   - Atalhos para as áreas operacionais do sistema
 *
 * KPIs financeiros (Folha mensal, Variação) ainda dependem do Bloco 2.
 */

import {
  ArrowRight,
  Briefcase,
  Building2,
  FileText,
  GraduationCap,
  Heart,
  HelpingHand,
  Landmark,
  Library,
  ShieldCheck,
  Sparkles,
  Tag,
  UserCircle,
  Users,
  Vote,
  Wallet,
} from "lucide-react";
import { Link } from "react-router-dom";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/lib/auth-context";
import { useDashboardKpis } from "@/lib/queries/kpis";

const ATALHOS = [
  {
    label: "Servidores",
    descricao: "Cadastro, admissão, vínculos",
    to: "/servidores",
    icon: Users,
  },
  { label: "Cargos", descricao: "Cargos públicos do município", to: "/cargos", icon: Briefcase },
  { label: "Lotações", descricao: "Secretarias e setores", to: "/lotacoes", icon: Library },
  { label: "Folha", descricao: "Competências e fechamento", to: "/folha", icon: Wallet },
  { label: "Rubricas", descricao: "Proventos e descontos", to: "/rubricas", icon: Tag },
  { label: "Relatórios", descricao: "eSocial, RAIS, DIRF", to: "/relatorios", icon: FileText },
];

const VINCULOS: Array<{
  label: string;
  regime: string;
  icon: typeof ShieldCheck;
  desc: string;
}> = [
  { label: "Efetivos", regime: "estatutario", icon: ShieldCheck, desc: "Concursados" },
  { label: "Comissionados", regime: "comissionado", icon: UserCircle, desc: "Cargo de confiança" },
  { label: "Contratados", regime: "temporario", icon: Sparkles, desc: "Temporários" },
  { label: "Eletivos", regime: "eletivo", icon: Vote, desc: "Prefeito, vice, vereadores" },
];

const AREAS: Array<{
  label: string;
  natureza: string;
  icon: typeof Heart;
}> = [
  { label: "Administração", natureza: "administracao", icon: Landmark },
  { label: "Saúde", natureza: "saude", icon: Heart },
  { label: "Educação", natureza: "educacao", icon: GraduationCap },
  { label: "Assistência social", natureza: "assistencia_social", icon: HelpingHand },
];

export default function DashboardPage() {
  const { user, activeTenant } = useAuth();
  const municipio = user?.municipios.find((m) => m.schema === activeTenant);
  const display = user?.nome_completo || user?.email || "";
  const kpis = useDashboardKpis();

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
        <p className="text-sm text-muted-foreground">
          {kpis.totalAtivos !== undefined ? (
            <>
              <span className="font-medium text-foreground tabular-nums">
                {kpis.totalAtivos.toLocaleString("pt-BR")}
              </span>{" "}
              servidores ativos no momento.
            </>
          ) : (
            <Skeleton className="h-4 w-44 inline-block" />
          )}
        </p>
      </header>

      {/* Por vínculo */}
      <section aria-labelledby="vinculo-heading" className="space-y-3">
        <h2
          id="vinculo-heading"
          className="text-[11px] uppercase tracking-wider font-medium text-muted-foreground"
        >
          Servidores por vínculo
        </h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {VINCULOS.map(({ label, regime, icon: Icon, desc }) => (
            <KpiCard
              key={regime}
              label={label}
              hint={desc}
              valor={kpis.porRegime[regime]}
              isLoading={kpis.isLoading}
              icon={Icon}
              to={`/servidores?regime=${regime}`}
            />
          ))}
        </div>
      </section>

      {/* Por área */}
      <section aria-labelledby="area-heading" className="space-y-3">
        <h2
          id="area-heading"
          className="text-[11px] uppercase tracking-wider font-medium text-muted-foreground"
        >
          Servidores por área
        </h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {AREAS.map(({ label, natureza, icon: Icon }) => (
            <KpiCard
              key={natureza}
              label={label}
              valor={kpis.porNatureza[natureza]}
              isLoading={kpis.isLoading}
              icon={Icon}
              to={`/servidores?natureza=${natureza}`}
            />
          ))}
        </div>
        {kpis.porNatureza["outros"] !== undefined && kpis.porNatureza["outros"]! > 0 && (
          <p className="text-xs text-muted-foreground">
            +{kpis.porNatureza["outros"]} servidor(es) em lotações classificadas como{" "}
            <Link to="/servidores?natureza=outros" className="underline">
              "Outros"
            </Link>{" "}
            (cultura, esporte, obras, etc., ou lotações sem classificação).
          </p>
        )}
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

interface KpiCardProps {
  label: string;
  hint?: string;
  valor: number | undefined;
  isLoading: boolean;
  icon: typeof Users;
  to: string;
}

function KpiCard({ label, hint, valor, isLoading, icon: Icon, to }: KpiCardProps) {
  return (
    <Link to={to} className="group">
      <Card className="h-full transition-colors group-hover:border-primary">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardDescription className="text-xs uppercase tracking-wider font-medium">
              {label}
            </CardDescription>
            <Icon className="h-4 w-4 text-muted-foreground" />
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {isLoading || valor === undefined ? (
            <Skeleton className="h-7 w-16" />
          ) : (
            <div
              className="font-semibold tabular-nums"
              style={{ fontSize: 24, letterSpacing: "-0.015em" }}
            >
              {valor.toLocaleString("pt-BR")}
            </div>
          )}
          <p className="text-xs text-muted-foreground mt-1">{hint ?? "ver lista"}</p>
        </CardContent>
      </Card>
    </Link>
  );
}
