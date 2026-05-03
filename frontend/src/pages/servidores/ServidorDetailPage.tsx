/**
 * ServidorDetailPage — Bloco 1.3c.
 *
 * Detalhe do servidor com 4 abas (Pessoais, Vínculos, Dependentes, Histórico)
 * e ações: editar dados pessoais, desligar, transferir vínculo, CRUD de
 * dependentes. Documentos ficam para uma onda futura (precisa upload com
 * FormData).
 */

import { useState, type ReactNode } from "react";
import {
  ArrowLeft,
  ArrowLeftRight,
  Briefcase,
  Building2,
  Calendar,
  CircleUser,
  History,
  Mail,
  MapPin,
  MoreHorizontal,
  PencilLine,
  Phone,
  Plus,
  PowerOff,
  Trash2,
  Users,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";
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
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { extractDomainErrorMessage } from "@/lib/api";
import { useDeleteDependente } from "@/lib/queries/dependentes";
import { useServidor, useServidorHistorico } from "@/lib/queries/servidores";
import type { ServidorDetail } from "@/types";

import { DependenteFormSheet } from "./DependenteFormSheet";
import { DesligamentoDialog } from "./DesligamentoDialog";
import { ServidorEditSheet } from "./ServidorEditSheet";
import { TransferenciaDialog } from "./TransferenciaDialog";

function formatCpf(cpf: string): string {
  const onlyDigits = cpf.replace(/\D/g, "").padStart(11, "0").slice(-11);
  return `${onlyDigits.slice(0, 3)}.${onlyDigits.slice(3, 6)}.${onlyDigits.slice(6, 9)}-${onlyDigits.slice(9, 11)}`;
}

function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const [y, m, d] = iso.split("T")[0].split("-");
  return `${d}/${m}/${y}`;
}

function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const dt = new Date(iso);
  return `${dt.toLocaleDateString("pt-BR")} ${dt.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}`;
}

export default function ServidorDetailPage() {
  const { id } = useParams<{ id: string }>();
  const servidorId = id ? Number(id) : null;

  const { data: servidor, isLoading, isError, error } = useServidor(servidorId);

  // Dialogs / Sheets state
  const [editOpen, setEditOpen] = useState(false);
  const [desligarOpen, setDesligarOpen] = useState(false);
  const [transferirVinculoId, setTransferirVinculoId] = useState<{
    id: number;
    lotacaoId: number;
    lotacaoNome: string;
  } | null>(null);
  const [dependenteFormOpen, setDependenteFormOpen] = useState(false);
  const [editingDependente, setEditingDependente] = useState<
    ServidorDetail["dependentes"][number] | null
  >(null);
  const [confirmDeleteDependente, setConfirmDeleteDependente] = useState<number | null>(
    null,
  );

  if (isLoading) return <DetailSkeleton />;
  if (isError) {
    return (
      <div className="space-y-4">
        <BackLink />
        <Card>
          <CardContent className="py-8 text-center text-sm text-destructive">
            {extractDomainErrorMessage(error) ?? "Falha ao carregar servidor."}
          </CardContent>
        </Card>
      </div>
    );
  }
  if (!servidor) return null;

  return (
    <div className="space-y-6">
      <BackLink />

      <header className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
        <div className="space-y-1">
          <h1 className="font-semibold inline-flex items-center gap-3" style={{ fontSize: 24 }}>
            <span className="inline-flex h-10 w-10 items-center justify-center rounded-md bg-primary-soft text-primary-soft-foreground">
              <CircleUser className="h-6 w-6" />
            </span>
            {servidor.nome}
          </h1>
          <div className="flex flex-wrap items-center gap-3 text-sm text-muted-foreground">
            <span className="font-mono text-xs tabular-nums">Mat. {servidor.matricula}</span>
            <span>·</span>
            <span className="font-mono text-xs">{formatCpf(servidor.cpf)}</span>
            <span>·</span>
            {servidor.ativo ? (
              <Badge variant="success">Ativo</Badge>
            ) : (
              <Badge variant="muted">Inativo</Badge>
            )}
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <Button variant="outline" onClick={() => setEditOpen(true)}>
            <PencilLine className="h-4 w-4 mr-1" /> Editar dados
          </Button>
          {servidor.ativo && (
            <Button
              variant="outline"
              onClick={() => setDesligarOpen(true)}
              className="text-destructive hover:text-destructive"
            >
              <PowerOff className="h-4 w-4 mr-1" /> Desligar
            </Button>
          )}
        </div>
      </header>

      <Tabs defaultValue="pessoais">
        <TabsList>
          <TabsTrigger value="pessoais">
            <CircleUser className="h-4 w-4 mr-1.5" /> Pessoais
          </TabsTrigger>
          <TabsTrigger value="vinculos">
            <Briefcase className="h-4 w-4 mr-1.5" /> Vínculos ({servidor.vinculos.length})
          </TabsTrigger>
          <TabsTrigger value="dependentes">
            <Users className="h-4 w-4 mr-1.5" /> Dependentes ({servidor.dependentes.length})
          </TabsTrigger>
          <TabsTrigger value="historico">
            <History className="h-4 w-4 mr-1.5" /> Histórico
          </TabsTrigger>
        </TabsList>

        <TabsContent value="pessoais">
          <PessoaisTab servidor={servidor} />
        </TabsContent>
        <TabsContent value="vinculos">
          <VinculosTab
            servidor={servidor}
            onTransferir={(v) =>
              setTransferirVinculoId({
                id: v.id,
                lotacaoId: v.lotacao,
                lotacaoNome: v.lotacao_nome ?? "",
              })
            }
          />
        </TabsContent>
        <TabsContent value="dependentes">
          <DependentesTab
            servidor={servidor}
            onNovo={() => {
              setEditingDependente(null);
              setDependenteFormOpen(true);
            }}
            onEditar={(d) => {
              setEditingDependente(d);
              setDependenteFormOpen(true);
            }}
            onExcluir={(id) => setConfirmDeleteDependente(id)}
          />
        </TabsContent>
        <TabsContent value="historico">
          {servidorId !== null && <HistoricoTab servidorId={servidorId} />}
        </TabsContent>
      </Tabs>

      {/* Dialogs / Sheets */}
      <ServidorEditSheet open={editOpen} onOpenChange={setEditOpen} servidor={servidor} />
      <DesligamentoDialog
        open={desligarOpen}
        onOpenChange={setDesligarOpen}
        servidorId={servidor.id}
        servidorNome={servidor.nome}
      />
      {transferirVinculoId && (
        <TransferenciaDialog
          open={transferirVinculoId !== null}
          onOpenChange={(o) => !o && setTransferirVinculoId(null)}
          vinculoId={transferirVinculoId.id}
          lotacaoAtualId={transferirVinculoId.lotacaoId}
          lotacaoAtualNome={transferirVinculoId.lotacaoNome}
        />
      )}
      <DependenteFormSheet
        open={dependenteFormOpen}
        onOpenChange={setDependenteFormOpen}
        servidorId={servidor.id}
        dependente={editingDependente}
      />
      <DeleteDependenteDialog
        open={confirmDeleteDependente !== null}
        onOpenChange={(o) => !o && setConfirmDeleteDependente(null)}
        dependenteId={confirmDeleteDependente}
      />
    </div>
  );
}

function BackLink() {
  return (
    <Link
      to="/servidores"
      className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground"
    >
      <ArrowLeft className="h-4 w-4" />
      Servidores
    </Link>
  );
}

function PessoaisTab({ servidor }: { servidor: ServidorDetail }) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Identificação</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-3">
          <Field label="Nome">{servidor.nome}</Field>
          <Field label="CPF" mono>
            {formatCpf(servidor.cpf)}
          </Field>
          <Field label="PIS/PASEP" mono>
            {servidor.pis_pasep || "—"}
          </Field>
          <Field label="Data de nascimento">
            <span className="inline-flex items-center gap-1.5">
              <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
              {formatDate(servidor.data_nascimento)}
            </span>
          </Field>
          <Field label="Sexo">{servidor.sexo_display || "—"}</Field>
          <Field label="Estado civil">{servidor.estado_civil_display || "—"}</Field>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Contato e endereço</CardTitle>
        </CardHeader>
        <CardContent className="text-sm space-y-3">
          <Field label="E-mail">
            {servidor.email ? (
              <span className="inline-flex items-center gap-1.5">
                <Mail className="h-3.5 w-3.5 text-muted-foreground" />
                {servidor.email}
              </span>
            ) : (
              "—"
            )}
          </Field>
          <Field label="Telefone">
            {servidor.telefone ? (
              <span className="inline-flex items-center gap-1.5">
                <Phone className="h-3.5 w-3.5 text-muted-foreground" />
                {servidor.telefone}
              </span>
            ) : (
              "—"
            )}
          </Field>
          <Field label="Logradouro">
            {servidor.logradouro
              ? `${servidor.logradouro}${servidor.numero ? ", " + servidor.numero : ""}${servidor.complemento ? " — " + servidor.complemento : ""}`
              : "—"}
          </Field>
          <Field label="Bairro">{servidor.bairro || "—"}</Field>
          <Field label="Cidade/UF">
            {servidor.cidade ? (
              <span className="inline-flex items-center gap-1.5">
                <MapPin className="h-3.5 w-3.5 text-muted-foreground" />
                {servidor.cidade}
                {servidor.uf ? ` / ${servidor.uf}` : ""}
              </span>
            ) : (
              "—"
            )}
          </Field>
          <Field label="CEP" mono>
            {servidor.cep || "—"}
          </Field>
        </CardContent>
      </Card>
    </div>
  );
}

function VinculosTab({
  servidor,
  onTransferir,
}: {
  servidor: ServidorDetail;
  onTransferir: (v: ServidorDetail["vinculos"][number]) => void;
}) {
  if (servidor.vinculos.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-sm text-muted-foreground">
          Este servidor não possui vínculos. Use a tela de admissão para criar o primeiro.
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {servidor.vinculos.map((v) => (
        <Card key={v.id}>
          <CardContent className="py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <Briefcase className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">{v.cargo_nome}</span>
                <Badge variant="muted">{v.regime_display}</Badge>
                {v.ativo ? (
                  <Badge variant="success">Ativo</Badge>
                ) : (
                  <Badge variant="muted">Encerrado</Badge>
                )}
              </div>
              <div className="text-sm text-muted-foreground inline-flex items-center gap-1.5">
                <Building2 className="h-3.5 w-3.5" />
                {v.lotacao_nome}
              </div>
              <div className="text-xs text-muted-foreground">
                Admissão: {formatDate(v.data_admissao)}
                {v.data_demissao && ` · Demissão: ${formatDate(v.data_demissao)}`}
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-xs text-muted-foreground">Salário-base</div>
                <div className="font-mono tabular-nums font-medium">
                  R${" "}
                  {Number(v.salario_base).toLocaleString("pt-BR", {
                    minimumFractionDigits: 2,
                  })}
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {v.carga_horaria}h semanais
                </div>
              </div>
              {v.ativo && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" aria-label="Ações do vínculo">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onTransferir(v)}>
                      <ArrowLeftRight className="h-4 w-4 mr-2" /> Transferir lotação
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function DependentesTab({
  servidor,
  onNovo,
  onEditar,
  onExcluir,
}: {
  servidor: ServidorDetail;
  onNovo: () => void;
  onEditar: (d: ServidorDetail["dependentes"][number]) => void;
  onExcluir: (id: number) => void;
}) {
  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <Button onClick={onNovo} size="sm">
          <Plus className="h-4 w-4 mr-1" /> Novo dependente
        </Button>
      </div>
      {servidor.dependentes.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-sm text-muted-foreground">
            Nenhum dependente cadastrado.
          </CardContent>
        </Card>
      ) : (
        servidor.dependentes.map((d) => (
          <Card key={d.id}>
            <CardContent className="py-3 flex items-center justify-between gap-3">
              <div>
                <div className="font-medium">{d.nome}</div>
                <div className="text-xs text-muted-foreground">
                  {d.parentesco} · Nascimento: {formatDate(d.data_nascimento)}
                </div>
              </div>
              <div className="flex items-center gap-2">
                {d.ir && <Badge variant="info">IR</Badge>}
                {d.salario_familia && <Badge variant="success">Sal. família</Badge>}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" aria-label="Ações do dependente">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem onClick={() => onEditar(d)}>
                      <PencilLine className="h-4 w-4 mr-2" /> Editar
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      onClick={() => onExcluir(d.id)}
                      className="text-destructive focus:text-destructive"
                    >
                      <Trash2 className="h-4 w-4 mr-2" /> Excluir
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </CardContent>
          </Card>
        ))
      )}
    </div>
  );
}

function HistoricoTab({ servidorId }: { servidorId: number }) {
  const { data, isLoading, isError, error } = useServidorHistorico(servidorId);

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-6 space-y-3">
          <Skeleton className="h-4 w-1/2" />
          <Skeleton className="h-4 w-3/4" />
          <Skeleton className="h-4 w-1/3" />
        </CardContent>
      </Card>
    );
  }

  if (isError) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-sm text-destructive">
          {extractDomainErrorMessage(error) ?? "Falha ao carregar histórico."}
        </CardContent>
      </Card>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center text-sm text-muted-foreground">
          Nenhuma entrada no histórico.
        </CardContent>
      </Card>
    );
  }

  const tipoLabel = (t: string) =>
    t === "+" ? "Criado" : t === "-" ? "Removido" : "Alterado";
  const tipoVariant = (t: string): "success" | "destructive" | "info" =>
    t === "+" ? "success" : t === "-" ? "destructive" : "info";

  return (
    <Card>
      <CardContent className="py-4">
        <ol className="relative border-l border-border ml-2 space-y-5">
          {data.map((entry) => (
            <li key={entry.history_id} className="ml-4">
              <span className="absolute -left-1.5 mt-1.5 h-3 w-3 rounded-full bg-primary" />
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <Badge variant={tipoVariant(entry.history_type)}>
                  {tipoLabel(entry.history_type)}
                </Badge>
                <span className="font-medium">{formatDateTime(entry.history_date)}</span>
                {entry.history_user_email && (
                  <span className="text-xs text-muted-foreground">
                    por {entry.history_user_email}
                  </span>
                )}
              </div>
              <div className="mt-1 text-xs text-muted-foreground">
                Snapshot: {entry.nome} · {formatCpf(entry.cpf)} · Mat. {entry.matricula}
                {entry.ativo ? " · Ativo" : " · Inativo"}
              </div>
              {entry.history_change_reason && (
                <p className="mt-1 text-sm">{entry.history_change_reason}</p>
              )}
            </li>
          ))}
        </ol>
      </CardContent>
    </Card>
  );
}

function DeleteDependenteDialog({
  open,
  onOpenChange,
  dependenteId,
}: {
  open: boolean;
  onOpenChange: (o: boolean) => void;
  dependenteId: number | null;
}) {
  const deleteMutation = useDeleteDependente();

  async function confirmar() {
    if (dependenteId === null) return;
    try {
      await deleteMutation.mutateAsync(dependenteId);
      toast.success("Dependente excluído.");
      onOpenChange(false);
    } catch (e) {
      toast.error(extractDomainErrorMessage(e) ?? "Falha ao excluir.");
    }
  }

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Excluir dependente?</AlertDialogTitle>
          <AlertDialogDescription>
            Esta ação não pode ser desfeita.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel disabled={deleteMutation.isPending}>Cancelar</AlertDialogCancel>
          <AlertDialogAction
            onClick={(e) => {
              e.preventDefault();
              confirmar();
            }}
            disabled={deleteMutation.isPending}
            className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
          >
            {deleteMutation.isPending ? "Excluindo..." : "Excluir"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

function Field({
  label,
  children,
  mono,
}: {
  label: string;
  children: ReactNode;
  mono?: boolean;
}) {
  return (
    <div className="grid grid-cols-[140px_1fr] gap-3 items-start">
      <dt className="text-xs uppercase tracking-wider text-muted-foreground pt-0.5">{label}</dt>
      <dd className={mono ? "font-mono text-sm" : "text-sm"}>{children}</dd>
    </div>
  );
}

function DetailSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-4 w-24" />
      <div className="space-y-2">
        <Skeleton className="h-7 w-72" />
        <Skeleton className="h-4 w-96" />
      </div>
      <Skeleton className="h-10 w-96" />
      <div className="grid gap-4 md:grid-cols-2">
        <Skeleton className="h-64" />
        <Skeleton className="h-64" />
      </div>
    </div>
  );
}
