/**
 * FolhaDetailPage — Onda 2.6.
 *
 * Tela principal da folha. Mostra header com totais, botão de calcular
 * (idempotente — mostra confirmação se já estiver calculada), relatório
 * do último cálculo (em sessão), e tabs com lançamentos / erros.
 */

import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import {
  ArrowLeft,
  Building2,
  CalendarDays,
  Calculator,
  CircleAlert,
  CircleCheck,
  FileText,
  ListChecks,
  RefreshCw,
  Tag,
  Users,
} from "lucide-react";
import { toast } from "sonner";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { extractDomainErrorMessage } from "@/lib/api";
import {
  abrirHoleritePdf,
  useCalcularFolha,
  useFolha,
  useLancamentosList,
  useResumoArea,
  useResumoServidores,
} from "@/lib/queries/folhas";
import type { ResumoAreaLinha } from "@/lib/queries/folhas";
import type { Folha, Lancamento, RelatorioCalculo } from "@/types";

import { ProgramacaoComplementarTab } from "./ProgramacaoComplementarTab";
import { ProgramacaoFeriasTab } from "./ProgramacaoFeriasTab";
import { ProgramacaoLicencaPremioTab } from "./ProgramacaoLicencaPremioTab";

const PAGE_SIZE = 50;

function statusBadgeVariant(
  status: Folha["status"],
): "secondary" | "info" | "warning" | "success" {
  if (status === "aberta") return "secondary";
  if (status === "calculada") return "info";
  if (status === "conferida") return "warning";
  return "success";
}

function fmtMoeda(s: string | number | null | undefined): string {
  if (s == null) return "—";
  const v = typeof s === "string" ? Number(s) : s;
  if (!Number.isFinite(v)) return "—";
  return v.toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

function fmtCompetencia(iso: string): string {
  const [y, m] = iso.split("-");
  const meses = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
  ];
  return `${meses[Number(m) - 1]} de ${y}`;
}

function rubricaTipoVariant(tipo: Lancamento["rubrica_tipo"]): "success" | "destructive" | "info" {
  if (tipo === "provento") return "success";
  if (tipo === "desconto") return "destructive";
  return "info";
}

export default function FolhaDetailPage() {
  const { id: idParam } = useParams<{ id: string }>();
  const id = idParam ? Number(idParam) : null;

  const { data: folha, isLoading: loadingFolha } = useFolha(id);
  const [confirmaOpen, setConfirmaOpen] = useState(false);
  const [relatorio, setRelatorio] = useState<RelatorioCalculo | null>(null);

  const [filtroServidor, setFiltroServidor] = useState("");
  const [filtroRubrica, setFiltroRubrica] = useState("");
  const [page, setPage] = useState(1);

  const calcMut = useCalcularFolha();
  const { data: lancamentos, isLoading: loadingLanc, refetch: refetchLanc } =
    useLancamentosList({
      folha: id ?? undefined,
      servidor_nome: filtroServidor || undefined,
      rubrica_codigo: filtroRubrica || undefined,
      page,
      page_size: PAGE_SIZE,
    });

  const { data: resumoServidores, isLoading: loadingServidores } = useResumoServidores(id);
  const { data: resumoArea, isLoading: loadingArea } = useResumoArea(id);

  const totalLanc = lancamentos?.count ?? 0;
  const totalPages = Math.max(1, Math.ceil(totalLanc / PAGE_SIZE));

  async function dispararCalculo() {
    if (id === null) return;
    setConfirmaOpen(false);
    try {
      const rel = await calcMut.mutateAsync(id);
      setRelatorio(rel);
      if (rel.erros.length === 0) {
        toast.success(
          `Folha calculada — ${rel.lancamentos_criados} criados, ${rel.lancamentos_atualizados} atualizados, ${rel.lancamentos_removidos} removidos.`,
        );
      } else {
        toast.warning(`Folha calculada com ${rel.erros.length} erro(s).`);
      }
      refetchLanc();
    } catch (e) {
      toast.error(extractDomainErrorMessage(e) ?? "Erro ao calcular folha.");
    }
  }

  const [holeriteVinculo, setHoleriteVinculo] = useState<number | null>(null);
  async function verHolerite(vinculoId: number) {
    if (id === null) return;
    setHoleriteVinculo(vinculoId);
    try {
      await abrirHoleritePdf(id, vinculoId);
    } catch (e) {
      toast.error(extractDomainErrorMessage(e) ?? "Não foi possível gerar o holerite.");
    } finally {
      setHoleriteVinculo(null);
    }
  }

  const podeRecalcular = useMemo(() => {
    if (!folha) return false;
    return folha.status !== "fechada";
  }, [folha]);

  if (loadingFolha) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-32 w-full" />
      </div>
    );
  }
  if (!folha) {
    return (
      <div className="space-y-2">
        <p className="text-sm text-muted-foreground">Folha não encontrada.</p>
        <Link to="/folha" className="text-sm underline">Voltar para a lista</Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <header className="space-y-3">
        <Link to="/folha" className="text-xs text-muted-foreground inline-flex items-center gap-1 hover:underline">
          <ArrowLeft className="h-3 w-3" /> Folhas
        </Link>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="font-semibold capitalize" style={{ fontSize: 22 }}>
              {folha.tipo_display} — {fmtCompetencia(folha.competencia)}
            </h1>
            <div className="mt-2 inline-flex items-center gap-2">
              <Badge variant={statusBadgeVariant(folha.status)}>{folha.status_display}</Badge>
              <span className="text-xs text-muted-foreground">
                {folha.lancamentos_count} lançamento{folha.lancamentos_count === 1 ? "" : "s"}
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => setConfirmaOpen(true)}
              disabled={!podeRecalcular || calcMut.isPending}
              className="gap-2"
            >
              {calcMut.isPending ? (
                <RefreshCw className="h-4 w-4 animate-spin" />
              ) : (
                <Calculator className="h-4 w-4" />
              )}
              {folha.status === "aberta" ? "Calcular folha" : "Recalcular"}
            </Button>
          </div>
        </div>
      </header>

      <div className="grid gap-3 sm:grid-cols-3">
        <Card>
          <CardContent className="py-4">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Proventos</p>
            <p className="text-xl font-mono font-medium mt-1">{fmtMoeda(folha.total_proventos)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Descontos</p>
            <p className="text-xl font-mono font-medium mt-1">{fmtMoeda(folha.total_descontos)}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="py-4">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Líquido</p>
            <p className="text-xl font-mono font-medium mt-1 text-primary">{fmtMoeda(folha.total_liquido)}</p>
          </CardContent>
        </Card>
      </div>

      {relatorio && <RelatorioCard relatorio={relatorio} onDismiss={() => setRelatorio(null)} />}

      <Tabs
        defaultValue={
          folha.tipo === "ferias" ||
          folha.tipo === "licenca_premio" ||
          folha.tipo === "complementar"
            ? "programacao"
            : "servidores"
        }
      >
        <TabsList>
          {(folha.tipo === "ferias" ||
            folha.tipo === "licenca_premio" ||
            folha.tipo === "complementar") && (
            <TabsTrigger value="programacao" className="gap-2">
              <CalendarDays className="h-3.5 w-3.5" /> Programação
            </TabsTrigger>
          )}
          <TabsTrigger value="servidores" className="gap-2">
            <Users className="h-3.5 w-3.5" /> Servidores
          </TabsTrigger>
          <TabsTrigger value="areas" className="gap-2">
            <Building2 className="h-3.5 w-3.5" /> Por área
          </TabsTrigger>
          <TabsTrigger value="lancamentos" className="gap-2">
            <ListChecks className="h-3.5 w-3.5" /> Lançamentos ({totalLanc})
          </TabsTrigger>
          <TabsTrigger value="erros" className="gap-2">
            <CircleAlert className="h-3.5 w-3.5" />
            Erros {relatorio ? `(${relatorio.erros.length})` : ""}
          </TabsTrigger>
          <TabsTrigger value="info" className="gap-2">
            <Tag className="h-3.5 w-3.5" /> Informações
          </TabsTrigger>
        </TabsList>

        {folha.tipo === "ferias" && id !== null && (
          <TabsContent value="programacao">
            <ProgramacaoFeriasTab folhaId={id} />
          </TabsContent>
        )}
        {folha.tipo === "licenca_premio" && id !== null && (
          <TabsContent value="programacao">
            <ProgramacaoLicencaPremioTab folhaId={id} />
          </TabsContent>
        )}
        {folha.tipo === "complementar" && id !== null && (
          <TabsContent value="programacao">
            <ProgramacaoComplementarTab folhaId={id} />
          </TabsContent>
        )}

        <TabsContent value="servidores" className="space-y-3">
          <div className="rounded-md border bg-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Servidor</TableHead>
                  <TableHead>Cargo / Lotação</TableHead>
                  <TableHead className="text-right">Proventos</TableHead>
                  <TableHead className="text-right">Descontos</TableHead>
                  <TableHead className="text-right">Líquido</TableHead>
                  <TableHead className="text-right">Holerite</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loadingServidores && Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={`sk-${i}`}>
                    {Array.from({ length: 6 }).map((_, j) => (
                      <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                    ))}
                  </TableRow>
                ))}
                {!loadingServidores && (resumoServidores?.length ?? 0) === 0 && (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                      Sem servidores nesta folha. Calcule a folha para gerar.
                    </TableCell>
                  </TableRow>
                )}
                {resumoServidores?.map((s) => (
                  <TableRow key={s.vinculo_id}>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="text-sm">{s.servidor_nome}</span>
                        <span className="text-xs text-muted-foreground font-mono">{s.servidor_matricula}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="text-sm">{s.cargo ?? "—"}</span>
                        <span className="text-xs text-muted-foreground">{s.lotacao ?? "—"}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right font-mono text-sm">{fmtMoeda(s.proventos)}</TableCell>
                    <TableCell className="text-right font-mono text-sm">{fmtMoeda(s.descontos)}</TableCell>
                    <TableCell className="text-right font-mono text-sm font-medium text-primary">{fmtMoeda(s.liquido)}</TableCell>
                    <TableCell className="text-right">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="gap-1.5 h-7"
                        disabled={holeriteVinculo === s.vinculo_id}
                        onClick={() => verHolerite(s.vinculo_id)}
                        title={`Holerite de ${s.servidor_nome}`}
                      >
                        <FileText className="h-3.5 w-3.5" /> PDF
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          {(resumoServidores?.length ?? 0) > 0 && (
            <p className="text-sm text-muted-foreground">
              {resumoServidores?.length} servidor{resumoServidores?.length === 1 ? "" : "es"} na competência.
            </p>
          )}
        </TabsContent>

        <TabsContent value="areas" className="space-y-4">
          {loadingArea && <Skeleton className="h-40 w-full" />}
          {resumoArea && (
            <>
              <AreaTable titulo="Por lotação" linhas={resumoArea.por_lotacao} />
              <AreaTable titulo="Por órgão emissor" linhas={resumoArea.por_orgao} />
              <Card className="border-primary/40 bg-primary-soft">
                <CardContent className="py-3 flex flex-wrap items-center justify-between gap-3 text-sm">
                  <span className="text-xs uppercase tracking-wide text-muted-foreground">Total geral</span>
                  <div className="flex gap-6 font-mono">
                    <span>Proventos: <strong>{fmtMoeda(resumoArea.geral.proventos)}</strong></span>
                    <span>Descontos: <strong>{fmtMoeda(resumoArea.geral.descontos)}</strong></span>
                    <span className="text-primary">Líquido: <strong>{fmtMoeda(resumoArea.geral.liquido)}</strong></span>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </TabsContent>

        <TabsContent value="lancamentos" className="space-y-3">
          <div className="flex gap-2 flex-wrap">
            <Input
              placeholder="Filtrar por nome do servidor…"
              value={filtroServidor}
              onChange={(e) => { setFiltroServidor(e.target.value); setPage(1); }}
              className="max-w-xs"
            />
            <Input
              placeholder="Código da rubrica (ex.: INSS)"
              value={filtroRubrica}
              onChange={(e) => { setFiltroRubrica(e.target.value); setPage(1); }}
              className="max-w-xs"
            />
          </div>

          <div className="rounded-md border bg-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Servidor</TableHead>
                  <TableHead>Rubrica</TableHead>
                  <TableHead>Tipo</TableHead>
                  <TableHead className="text-right">Valor</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loadingLanc && Array.from({ length: 5 }).map((_, i) => (
                  <TableRow key={`skel-${i}`}>
                    {Array.from({ length: 4 }).map((_, j) => (
                      <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                    ))}
                  </TableRow>
                ))}
                {!loadingLanc && lancamentos?.results.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={4} className="text-center py-8 text-muted-foreground">
                      Sem lançamentos. Clique em "Calcular folha" para gerar.
                    </TableCell>
                  </TableRow>
                )}
                {lancamentos?.results.map((l) => (
                  <TableRow key={l.id}>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="text-sm">{l.servidor_nome}</span>
                        <span className="text-xs text-muted-foreground font-mono">{l.servidor_matricula}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-col">
                        <span className="text-sm">{l.rubrica_nome}</span>
                        <span className="text-xs text-muted-foreground font-mono">{l.rubrica_codigo}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={rubricaTipoVariant(l.rubrica_tipo)}>{l.rubrica_tipo}</Badge>
                    </TableCell>
                    <TableCell className="text-right font-mono text-sm">{fmtMoeda(l.valor)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>

          {totalLanc > 0 && (
            <div className="flex items-center justify-between text-sm text-muted-foreground">
              <span>{totalLanc} lançamento{totalLanc === 1 ? "" : "s"}</span>
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => Math.max(1, p - 1))}>
                  Anterior
                </Button>
                <span>Página {page} de {totalPages}</span>
                <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                  Próxima
                </Button>
              </div>
            </div>
          )}
        </TabsContent>

        <TabsContent value="erros">
          {!relatorio || relatorio.erros.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground text-sm">
              <CircleCheck className="h-8 w-8 mx-auto mb-2 text-green-600" />
              Nenhum erro reportado.
            </div>
          ) : (
            <div className="rounded-md border bg-card divide-y">
              {relatorio.erros.map((er, i) => (
                <div key={i} className="p-3 text-sm">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge variant="destructive" className="font-mono text-[10px]">{er.code}</Badge>
                    <span className="font-medium">{er.matricula}</span>
                    <span className="text-muted-foreground">·</span>
                    <span className="font-mono text-xs">{er.rubrica_codigo}</span>
                  </div>
                  <p className="text-xs text-muted-foreground">{er.mensagem}</p>
                </div>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="info">
          <Card>
            <CardContent className="py-4 space-y-3 text-sm">
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">Observações</p>
                <p className="mt-1">{folha.observacoes || "—"}</p>
              </div>
              <div className="grid grid-cols-2 gap-3 pt-2 text-xs text-muted-foreground">
                <div>
                  <span className="block uppercase tracking-wide">Criada em</span>
                  <span className="text-foreground">{folha.criado_em}</span>
                </div>
                <div>
                  <span className="block uppercase tracking-wide">Atualizada em</span>
                  <span className="text-foreground">{folha.atualizado_em}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <AlertDialog open={confirmaOpen} onOpenChange={setConfirmaOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {folha.status === "aberta" ? "Calcular folha?" : "Recalcular folha?"}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {folha.status === "aberta" ? (
                <>
                  O sistema vai percorrer todos os servidores ativos da competência
                  e calcular cada rubrica. Idempotente — pode rodar várias vezes
                  sem duplicar.
                </>
              ) : (
                <>
                  Esta folha já foi calculada uma vez. Recalcular vai{" "}
                  <strong>atualizar</strong> os valores existentes e{" "}
                  <strong>remover</strong> lançamentos de rubricas que deixaram
                  de ser ativas — sem duplicar nada.
                </>
              )}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={dispararCalculo}>
              {folha.status === "aberta" ? "Calcular" : "Recalcular"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

// ============================================================
// Tabela de totais por área (lotação / órgão)
// ============================================================

function AreaTable({ titulo, linhas }: { titulo: string; linhas: ResumoAreaLinha[] }) {
  return (
    <div className="space-y-1.5">
      <p className="text-xs uppercase tracking-wide text-muted-foreground">{titulo}</p>
      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Área</TableHead>
              <TableHead className="text-right">Proventos</TableHead>
              <TableHead className="text-right">Descontos</TableHead>
              <TableHead className="text-right">Líquido</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {linhas.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="text-center py-6 text-muted-foreground text-sm">
                  Sem dados.
                </TableCell>
              </TableRow>
            )}
            {linhas.map((l) => (
              <TableRow key={`${titulo}-${l.id ?? "none"}`}>
                <TableCell className="text-sm">{l.nome}</TableCell>
                <TableCell className="text-right font-mono text-sm">{fmtMoeda(l.proventos)}</TableCell>
                <TableCell className="text-right font-mono text-sm">{fmtMoeda(l.descontos)}</TableCell>
                <TableCell className="text-right font-mono text-sm font-medium text-primary">{fmtMoeda(l.liquido)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}

// ============================================================
// Card do relatório do último cálculo (em memória, não persistido)
// ============================================================

function RelatorioCard({
  relatorio,
  onDismiss,
}: {
  relatorio: RelatorioCalculo;
  onDismiss: () => void;
}) {
  const total = relatorio.lancamentos_criados + relatorio.lancamentos_atualizados;
  return (
    <Card className="border-primary/40 bg-primary-soft">
      <CardContent className="py-4 space-y-2">
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Último cálculo</p>
            <p className="text-sm">
              <strong>{relatorio.vinculos_processados}</strong> vínculos
              {" × "}
              <strong>{relatorio.rubricas_processadas}</strong> rubricas
              {" → "}
              <strong>{total}</strong> lançamento{total === 1 ? "" : "s"}
            </p>
            <p className="text-xs text-muted-foreground">
              {relatorio.lancamentos_criados} novos · {relatorio.lancamentos_atualizados} atualizados ·{" "}
              {relatorio.lancamentos_removidos} removidos · {relatorio.erros.length} erro(s)
            </p>
          </div>
          <Button variant="ghost" size="sm" onClick={onDismiss}>Ocultar</Button>
        </div>
        <details className="text-xs">
          <summary className="cursor-pointer text-muted-foreground">
            Ordem das rubricas calculadas
          </summary>
          <p className="font-mono mt-1 pl-3 border-l-2 border-primary/30">
            {relatorio.ordem_rubricas.join(" → ")}
          </p>
        </details>
      </CardContent>
    </Card>
  );
}
