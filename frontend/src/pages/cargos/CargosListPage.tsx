/**
 * CargosListPage — Bloco 1.3b.
 *
 * Listagem de cargos com:
 *   - Busca textual (codigo/nome/cbo) — debounce 300ms
 *   - Filtro por status (Todos/Ativos/Inativos)
 *   - Ordenação clicável por nome/código
 *   - Paginação default DRF (page=N)
 *   - Ações por linha (editar / desativar-ativar / excluir)
 */

import { useState, useEffect, useMemo } from "react";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  Briefcase,
  MoreHorizontal,
  Plus,
  Search,
  Trash2,
  PencilLine,
  Power,
  PowerOff,
} from "lucide-react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
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
  useCargo,
  useCargosList,
  useDeleteCargo,
  useUpdateCargo,
  type CargosListParams,
} from "@/lib/queries/cargos";
import type { Cargo } from "@/types";

import { CargoFormSheet } from "./CargoFormSheet";

const PAGE_SIZE = 20; // alinhado ao default do DRF (apps/core/pagination ou settings)

type StatusFilter = "todos" | "ativos" | "inativos";

function useDebounced<T>(value: T, delayMs = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(t);
  }, [value, delayMs]);
  return debounced;
}

export default function CargosListPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<StatusFilter>("todos");
  const [orderBy, setOrderBy] = useState<"nome" | "codigo" | "criado_em">("nome");
  const [orderDir, setOrderDir] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);

  const debouncedSearch = useDebounced(search);
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, status, orderBy, orderDir]);

  const params: CargosListParams = useMemo(
    () => ({
      search: debouncedSearch,
      ativo: status === "todos" ? undefined : status === "ativos",
      ordering: `${orderDir === "desc" ? "-" : ""}${orderBy}`,
      page,
    }),
    [debouncedSearch, status, orderBy, orderDir, page],
  );

  const { data, isLoading, isError, error, isFetching } = useCargosList(params);

  // Form sheet state (create + edit)
  const [formOpen, setFormOpen] = useState(false);
  const [editingId, setEditingId] = useState<number | null>(null);
  const editingQuery = useCargo(editingId);

  // Delete confirmation
  const [confirmDeleteId, setConfirmDeleteId] = useState<number | null>(null);
  const deleteMutation = useDeleteCargo();
  const updateMutation = useUpdateCargo();

  function abrirNovo() {
    setEditingId(null);
    setFormOpen(true);
  }

  function abrirEdicao(cargo: Cargo) {
    setEditingId(cargo.id);
    setFormOpen(true);
  }

  async function toggleAtivo(cargo: Cargo) {
    try {
      await updateMutation.mutateAsync({ id: cargo.id, payload: { ativo: !cargo.ativo } });
      toast.success(cargo.ativo ? "Cargo desativado." : "Cargo ativado.");
    } catch (e) {
      toast.error(extractDomainErrorMessage(e) ?? "Falha ao atualizar.");
    }
  }

  async function confirmarExclusao() {
    if (confirmDeleteId === null) return;
    try {
      await deleteMutation.mutateAsync(confirmDeleteId);
      toast.success("Cargo excluído.");
      setConfirmDeleteId(null);
    } catch (e) {
      toast.error(extractDomainErrorMessage(e) ?? "Não foi possível excluir.");
    }
  }

  function ordenarPor(coluna: "nome" | "codigo") {
    if (orderBy === coluna) {
      setOrderDir(orderDir === "asc" ? "desc" : "asc");
    } else {
      setOrderBy(coluna);
      setOrderDir("asc");
    }
  }

  const totalPages = data ? Math.max(1, Math.ceil(data.count / PAGE_SIZE)) : 1;

  return (
    <div className="space-y-6">
      <header className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div className="space-y-1">
          <h1 className="font-semibold inline-flex items-center gap-2" style={{ fontSize: 22 }}>
            <Briefcase className="h-5 w-5 text-muted-foreground" />
            Cargos
          </h1>
          <p className="text-sm text-muted-foreground">
            Cargos públicos cadastrados no município ativo.
          </p>
        </div>
        <Button onClick={abrirNovo} className="self-start sm:self-auto">
          <Plus className="h-4 w-4 mr-1" />
          Novo cargo
        </Button>
      </header>

      <div className="flex flex-col sm:flex-row gap-3 sm:items-center">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            type="search"
            placeholder="Buscar por código, nome ou CBO..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <Select value={status} onValueChange={(v) => setStatus(v as StatusFilter)}>
          <SelectTrigger className="w-full sm:w-44">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="todos">Todos os status</SelectItem>
            <SelectItem value="ativos">Apenas ativos</SelectItem>
            <SelectItem value="inativos">Apenas inativos</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="rounded-md border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[160px]">
                <button
                  type="button"
                  onClick={() => ordenarPor("codigo")}
                  className="inline-flex items-center gap-1 hover:text-foreground"
                >
                  Código <SortIcon active={orderBy === "codigo"} dir={orderDir} />
                </button>
              </TableHead>
              <TableHead>
                <button
                  type="button"
                  onClick={() => ordenarPor("nome")}
                  className="inline-flex items-center gap-1 hover:text-foreground"
                >
                  Nome <SortIcon active={orderBy === "nome"} dir={orderDir} />
                </button>
              </TableHead>
              <TableHead className="w-[180px]">Escolaridade</TableHead>
              <TableHead className="w-[120px]">Status</TableHead>
              <TableHead className="w-[64px]"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading && <SkeletonRows />}
            {isError && (
              <TableRow>
                <TableCell colSpan={5} className="py-12 text-center text-sm text-destructive">
                  {extractDomainErrorMessage(error) ?? "Falha ao carregar cargos."}
                </TableCell>
              </TableRow>
            )}
            {!isLoading && !isError && data?.results.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} className="py-16 text-center">
                  <div className="flex flex-col items-center gap-3 text-muted-foreground">
                    <Briefcase className="h-8 w-8" />
                    <div>
                      <p className="font-medium text-foreground">Nenhum cargo encontrado.</p>
                      <p className="text-xs mt-1">
                        {debouncedSearch || status !== "todos"
                          ? "Tente ajustar os filtros."
                          : "Comece criando o primeiro cargo do município."}
                      </p>
                    </div>
                  </div>
                </TableCell>
              </TableRow>
            )}
            {data?.results.map((cargo) => (
              <TableRow key={cargo.id}>
                <TableCell className="font-mono text-xs tabular-nums">{cargo.codigo}</TableCell>
                <TableCell className="font-medium">{cargo.nome}</TableCell>
                <TableCell>
                  <Badge variant="muted">{cargo.nivel_escolaridade_display}</Badge>
                </TableCell>
                <TableCell>
                  {cargo.ativo ? (
                    <Badge variant="success">Ativo</Badge>
                  ) : (
                    <Badge variant="muted">Inativo</Badge>
                  )}
                </TableCell>
                <TableCell className="text-right">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" aria-label="Ações do cargo">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => abrirEdicao(cargo)}>
                        <PencilLine className="h-4 w-4 mr-2" /> Editar
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => toggleAtivo(cargo)}>
                        {cargo.ativo ? (
                          <>
                            <PowerOff className="h-4 w-4 mr-2" /> Desativar
                          </>
                        ) : (
                          <>
                            <Power className="h-4 w-4 mr-2" /> Ativar
                          </>
                        )}
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => setConfirmDeleteId(cargo.id)}
                        className="text-destructive focus:text-destructive"
                      >
                        <Trash2 className="h-4 w-4 mr-2" /> Excluir
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {data && data.count > 0 && (
        <footer className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-sm text-muted-foreground">
          <span>
            {data.count} cargo{data.count === 1 ? "" : "s"}
            {isFetching && " · atualizando..."}
          </span>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={!data.previous}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              Anterior
            </Button>
            <span className="tabular-nums px-2">
              Página {page} de {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={!data.next}
              onClick={() => setPage((p) => p + 1)}
            >
              Próxima
            </Button>
          </div>
        </footer>
      )}

      <CargoFormSheet
        open={formOpen}
        onOpenChange={setFormOpen}
        cargo={editingId ? (editingQuery.data ?? null) : null}
      />

      <AlertDialog
        open={confirmDeleteId !== null}
        onOpenChange={(o) => !o && setConfirmDeleteId(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir cargo?</AlertDialogTitle>
            <AlertDialogDescription>
              Esta ação não pode ser desfeita. Cargos com vínculos existentes não podem ser
              excluídos — desative-os em vez disso.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleteMutation.isPending}>Cancelar</AlertDialogCancel>
            <AlertDialogAction
              onClick={(e) => {
                e.preventDefault();
                confirmarExclusao();
              }}
              disabled={deleteMutation.isPending}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleteMutation.isPending ? "Excluindo..." : "Excluir"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

function SortIcon({ active, dir }: { active: boolean; dir: "asc" | "desc" }) {
  if (!active) return <ArrowUpDown className="h-3 w-3 opacity-50" />;
  return dir === "asc" ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />;
}

function SkeletonRows() {
  return (
    <>
      {Array.from({ length: 6 }).map((_, i) => (
        <TableRow key={`skel-${i}`}>
          <TableCell>
            <Skeleton className="h-4 w-24" />
          </TableCell>
          <TableCell>
            <Skeleton className="h-4 w-64" />
          </TableCell>
          <TableCell>
            <Skeleton className="h-5 w-24" />
          </TableCell>
          <TableCell>
            <Skeleton className="h-5 w-16" />
          </TableCell>
          <TableCell>
            <Skeleton className="h-8 w-8 ml-auto" />
          </TableCell>
        </TableRow>
      ))}
    </>
  );
}
