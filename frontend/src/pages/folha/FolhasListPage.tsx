/**
 * FolhasListPage — Onda 2.6.
 *
 * Lista de folhas (mensais, 13º, férias, etc.) com filtros por ano/mês/tipo/status.
 * Cada linha clica para o detalhe (FolhaDetailPage). Ação "Calcular" também
 * disponível direto na linha pra agilidade.
 *
 * Permissões: read = qualquer papel, escrever/calcular = financeiro/admin/staff.
 */

import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Calculator,
  MoreHorizontal,
  PencilLine,
  Plus,
  Trash2,
  Wallet,
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { extractDomainErrorMessage } from "@/lib/api";
import {
  useCalcularFolha,
  useDeleteFolha,
  useFolha,
  useFolhasList,
  type FolhasListParams,
} from "@/lib/queries/folhas";
import type { Folha } from "@/types";

import { FolhaFormSheet } from "./FolhaFormSheet";

const PAGE_SIZE = 20;

const ANOS = [2024, 2025, 2026, 2027];
const MESES = [
  { v: "", label: "Todos os meses" },
  { v: "1", label: "Janeiro" },
  { v: "2", label: "Fevereiro" },
  { v: "3", label: "Março" },
  { v: "4", label: "Abril" },
  { v: "5", label: "Maio" },
  { v: "6", label: "Junho" },
  { v: "7", label: "Julho" },
  { v: "8", label: "Agosto" },
  { v: "9", label: "Setembro" },
  { v: "10", label: "Outubro" },
  { v: "11", label: "Novembro" },
  { v: "12", label: "Dezembro" },
];

const TIPOS = [
  { v: "", label: "Todos os tipos" },
  { v: "mensal", label: "Mensal" },
  { v: "13_primeira", label: "13º — 1ª parcela" },
  { v: "13_segunda", label: "13º — 2ª parcela" },
  { v: "ferias", label: "Férias" },
  { v: "rescisao", label: "Rescisão" },
  { v: "complementar", label: "Complementar" },
];

const STATUS = [
  { v: "", label: "Todos os status" },
  { v: "aberta", label: "Aberta" },
  { v: "calculada", label: "Calculada" },
  { v: "conferida", label: "Conferida" },
  { v: "fechada", label: "Fechada" },
];

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
  // YYYY-MM-DD → MM/YYYY
  const [y, m] = iso.split("-");
  return `${m}/${y}`;
}

export default function FolhasListPage() {
  const navigate = useNavigate();
  const [ano, setAno] = useState<string>(String(new Date().getFullYear()));
  const [mes, setMes] = useState<string>("");
  const [tipo, setTipo] = useState<string>("");
  const [status, setStatus] = useState<string>("");
  const [page, setPage] = useState(1);

  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const params: FolhasListParams = {
    ano: ano ? Number(ano) : undefined,
    mes: mes ? Number(mes) : undefined,
    tipo: tipo || undefined,
    status: status || undefined,
    page,
  };

  const { data, isLoading, isError, refetch } = useFolhasList(params);
  const folhasEditing = useFolha(editingId);
  const deleteMut = useDeleteFolha();
  const calcMut = useCalcularFolha();

  function openNew() {
    setEditingId(null);
    setFormOpen(true);
  }

  function openEdit(id: number) {
    setEditingId(id);
    setFormOpen(true);
  }

  async function onCalcular(id: number) {
    try {
      const rel = await calcMut.mutateAsync(id);
      if (rel.erros.length === 0) {
        toast.success(
          `Folha calculada — ${rel.lancamentos_criados} criados, ${rel.lancamentos_atualizados} atualizados.`,
        );
      } else {
        toast.warning(
          `Folha calculada com ${rel.erros.length} erro(s). Veja o detalhe.`,
        );
      }
    } catch (e) {
      toast.error(extractDomainErrorMessage(e) ?? "Erro ao calcular folha.");
    }
  }

  async function onDelete() {
    if (deletingId === null) return;
    try {
      await deleteMut.mutateAsync(deletingId);
      toast.success("Folha removida.");
      setDeletingId(null);
    } catch (e) {
      toast.error(extractDomainErrorMessage(e) ?? "Erro ao remover folha.");
    }
  }

  const total = data?.count ?? 0;
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <div className="space-y-4">
      <header className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="font-semibold inline-flex items-center gap-2" style={{ fontSize: 22 }}>
            <Wallet className="h-5 w-5 text-muted-foreground" />
            Folha de pagamento
          </h1>
          <p className="text-sm text-muted-foreground">
            Folhas mensais, 13º, férias e rescisões. Clique numa folha para detalhe e cálculo.
          </p>
        </div>
        <Button onClick={openNew} className="gap-2">
          <Plus className="h-4 w-4" /> Nova folha
        </Button>
      </header>

      <div className="flex flex-wrap gap-2 items-center bg-card rounded-md border p-3">
        <Select value={ano} onValueChange={(v) => { setAno(v); setPage(1); }}>
          <SelectTrigger className="w-32"><SelectValue placeholder="Ano" /></SelectTrigger>
          <SelectContent>
            {ANOS.map((a) => <SelectItem key={a} value={String(a)}>{a}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={mes || "todos"} onValueChange={(v) => { setMes(v === "todos" ? "" : v); setPage(1); }}>
          <SelectTrigger className="w-40"><SelectValue placeholder="Mês" /></SelectTrigger>
          <SelectContent>
            {MESES.map((m) => <SelectItem key={m.v || "todos"} value={m.v || "todos"}>{m.label}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={tipo || "todos"} onValueChange={(v) => { setTipo(v === "todos" ? "" : v); setPage(1); }}>
          <SelectTrigger className="w-48"><SelectValue placeholder="Tipo" /></SelectTrigger>
          <SelectContent>
            {TIPOS.map((t) => <SelectItem key={t.v || "todos"} value={t.v || "todos"}>{t.label}</SelectItem>)}
          </SelectContent>
        </Select>
        <Select value={status || "todos"} onValueChange={(v) => { setStatus(v === "todos" ? "" : v); setPage(1); }}>
          <SelectTrigger className="w-40"><SelectValue placeholder="Status" /></SelectTrigger>
          <SelectContent>
            {STATUS.map((s) => <SelectItem key={s.v || "todos"} value={s.v || "todos"}>{s.label}</SelectItem>)}
          </SelectContent>
        </Select>
      </div>

      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-32">Competência</TableHead>
              <TableHead>Tipo</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Proventos</TableHead>
              <TableHead className="text-right">Descontos</TableHead>
              <TableHead className="text-right">Líquido</TableHead>
              <TableHead className="text-right">Lançamentos</TableHead>
              <TableHead className="w-12"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading && Array.from({ length: 5 }).map((_, i) => (
              <TableRow key={`skel-${i}`}>
                {Array.from({ length: 8 }).map((_, j) => (
                  <TableCell key={j}><Skeleton className="h-4 w-full" /></TableCell>
                ))}
              </TableRow>
            ))}
            {isError && (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-8 text-destructive">
                  Erro ao carregar folhas.{" "}
                  <button onClick={() => refetch()} className="underline">Tentar novamente</button>
                </TableCell>
              </TableRow>
            )}
            {!isLoading && !isError && data?.results.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} className="text-center py-8 text-muted-foreground">
                  Nenhuma folha para os filtros selecionados.
                </TableCell>
              </TableRow>
            )}
            {data?.results.map((f) => (
              <TableRow
                key={f.id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => navigate(`/folha/${f.id}`)}
              >
                <TableCell className="font-mono text-xs">{fmtCompetencia(f.competencia)}</TableCell>
                <TableCell>{f.tipo_display}</TableCell>
                <TableCell>
                  <Badge variant={statusBadgeVariant(f.status)}>{f.status_display}</Badge>
                </TableCell>
                <TableCell className="text-right font-mono text-xs">{fmtMoeda(f.total_proventos)}</TableCell>
                <TableCell className="text-right font-mono text-xs">{fmtMoeda(f.total_descontos)}</TableCell>
                <TableCell className="text-right font-mono text-xs font-medium">{fmtMoeda(f.total_liquido)}</TableCell>
                <TableCell className="text-right text-xs">{f.lancamentos_count}</TableCell>
                <TableCell onClick={(e) => e.stopPropagation()}>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onSelect={() => onCalcular(f.id)} disabled={calcMut.isPending}>
                        <Calculator className="mr-2 h-4 w-4" /> Calcular
                      </DropdownMenuItem>
                      <DropdownMenuItem onSelect={() => openEdit(f.id)}>
                        <PencilLine className="mr-2 h-4 w-4" /> Editar
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        className="text-destructive focus:text-destructive"
                        onSelect={() => setDeletingId(f.id)}
                      >
                        <Trash2 className="mr-2 h-4 w-4" /> Remover
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {total > 0 && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>{total} folha{total === 1 ? "" : "s"}</span>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Anterior
            </Button>
            <span>Página {page} de {totalPages}</span>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
            >
              Próxima
            </Button>
          </div>
        </div>
      )}

      <FolhaFormSheet
        open={formOpen}
        onOpenChange={setFormOpen}
        folha={editingId ? folhasEditing.data ?? null : null}
      />

      <AlertDialog open={deletingId !== null} onOpenChange={(o) => !o && setDeletingId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remover folha?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação remove a folha e todos os seus lançamentos. Não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={onDelete} className="bg-destructive">
              Remover
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
