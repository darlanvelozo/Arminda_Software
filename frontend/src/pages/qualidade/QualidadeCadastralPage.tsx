/**
 * QualidadeCadastralPage — Onda 1.6b.
 *
 * Dashboard de saúde do cadastro do município para o eSocial.
 * Mostra:
 *  - Score médio (0-100) com indicador visual
 *  - Total de servidores completos vs. incompletos
 *  - Breakdown: quais campos faltam em mais cadastros (top 8)
 *  - Atalho pra filtrar a lista de servidores pelo campo selecionado
 */

import { useNavigate } from "react-router-dom";
import { CheckCircle2, FileWarning, Loader2, ShieldCheck } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useQualidadeResumo } from "@/lib/queries/servidores";

export default function QualidadeCadastralPage() {
  const navigate = useNavigate();
  const { data, isLoading, isError } = useQualidadeResumo();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-72" />
        <div className="grid gap-3 sm:grid-cols-3">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="rounded-md border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
        Falha ao carregar o resumo de qualidade cadastral.
      </div>
    );
  }

  const scoreColor =
    data.score_medio >= 90
      ? "text-emerald-600"
      : data.score_medio >= 70
        ? "text-amber-600"
        : "text-rose-600";

  const pctIncompletos =
    data.total_servidores > 0
      ? Math.round((100 * data.incompletos) / data.total_servidores)
      : 0;

  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="font-semibold inline-flex items-center gap-2" style={{ fontSize: 22 }}>
          <ShieldCheck className="h-5 w-5 text-muted-foreground" />
          Qualidade cadastral
        </h1>
        <p className="text-sm text-muted-foreground max-w-2xl">
          Avalia se cada servidor tem todos os campos exigidos pelo eSocial (S-1005 e S-2200).
          Use os atalhos abaixo para filtrar e completar o que falta antes da primeira remessa.
        </p>
      </header>

      <div className="grid gap-3 sm:grid-cols-3">
        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Score médio</CardDescription>
            <CardTitle className={`text-4xl font-semibold tabular-nums ${scoreColor}`}>
              {data.score_medio}
              <span className="text-base text-muted-foreground">/100</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-2 rounded-full bg-muted overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${
                  data.score_medio >= 90
                    ? "bg-emerald-500"
                    : data.score_medio >= 70
                      ? "bg-amber-500"
                      : "bg-rose-500"
                }`}
                style={{ width: `${data.score_medio}%` }}
              />
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardDescription>Cadastros completos</CardDescription>
            <CardTitle className="text-4xl font-semibold tabular-nums inline-flex items-center gap-2">
              <CheckCircle2 className="h-7 w-7 text-emerald-500" />
              {data.completos}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground">
            de {data.total_servidores} servidor{data.total_servidores === 1 ? "" : "es"} no município
          </CardContent>
        </Card>

        <Card className="cursor-pointer hover:border-primary/40" onClick={() => navigate("/servidores?cadastro=incompletos")}>
          <CardHeader className="pb-2">
            <CardDescription>Cadastros incompletos</CardDescription>
            <CardTitle className="text-4xl font-semibold tabular-nums inline-flex items-center gap-2 text-rose-600">
              <FileWarning className="h-7 w-7" />
              {data.incompletos}
            </CardTitle>
          </CardHeader>
          <CardContent className="text-xs text-muted-foreground inline-flex items-center gap-2">
            <span>{pctIncompletos}% do total</span>
            <Badge variant="muted">Clique para listar →</Badge>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Campos mais pendentes</CardTitle>
          <CardDescription>
            Ranking dos campos pré-eSocial que mais aparecem em branco no município.
            Preencher os 3 mais críticos costuma reduzir as rejeições estruturais em 60-80%.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {data.breakdown_campos_faltantes.length === 0 ? (
            <div className="rounded-md border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800 inline-flex items-center gap-2">
              <CheckCircle2 className="h-5 w-5" />
              Tudo certo. Nenhum campo crítico em branco — você está pronto para gerar S-2200.
            </div>
          ) : (
            <ul className="space-y-2">
              {data.breakdown_campos_faltantes.slice(0, 10).map((b) => {
                const pct =
                  data.total_servidores > 0
                    ? Math.round((100 * b.servidores_pendentes) / data.total_servidores)
                    : 0;
                return (
                  <li
                    key={b.campo}
                    className="flex items-center justify-between gap-4 rounded-md border bg-card px-3 py-2"
                  >
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium">{b.label}</div>
                      <div className="text-xs text-muted-foreground font-mono">{b.campo}</div>
                    </div>
                    <div className="flex items-center gap-3 text-xs">
                      <div className="w-24 h-2 rounded-full bg-muted overflow-hidden">
                        <div
                          className="h-full rounded-full bg-rose-400"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                      <span className="tabular-nums w-20 text-right text-muted-foreground">
                        {b.servidores_pendentes} ({pct}%)
                      </span>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>

      <div className="flex flex-col sm:flex-row gap-2">
        <Button
          variant="outline"
          onClick={() => navigate("/servidores?cadastro=incompletos")}
          className="flex-1"
        >
          <FileWarning className="h-4 w-4 mr-1" />
          Ver servidores com cadastro incompleto
        </Button>
        <Button
          variant="outline"
          onClick={() => navigate("/importar")}
          className="flex-1"
        >
          <Loader2 className="h-4 w-4 mr-1" />
          Importar planilha de enriquecimento
        </Button>
      </div>
    </div>
  );
}
