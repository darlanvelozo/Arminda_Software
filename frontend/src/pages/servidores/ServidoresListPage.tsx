/**
 * ServidoresListPage — Bloco 1.3b.
 *
 * Lista paginada de servidores com busca, filtro por status e ação de admissão.
 * Cada linha leva ao detalhe (/servidores/:id).
 */

import { useEffect, useMemo, useState } from "react";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  Plus,
  Search,
  Users,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
import { useServidoresList, type ServidoresListParams } from "@/lib/queries/servidores";

import { ServidorAdmissaoSheet } from "./ServidorAdmissaoSheet";

const PAGE_SIZE = 20;

type StatusFilter = "todos" | "ativos" | "inativos";

function useDebounced<T>(value: T, delayMs = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(t);
  }, [value, delayMs]);
  return debounced;
}

function formatCpf(cpf: string): string {
  const onlyDigits = cpf.replace(/\D/g, "").padStart(11, "0").slice(-11);
  return `${onlyDigits.slice(0, 3)}.${onlyDigits.slice(3, 6)}.${onlyDigits.slice(6, 9)}-${onlyDigits.slice(9, 11)}`;
}

export default function ServidoresListPage() {
  const navigate = useNavigate();

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState<StatusFilter>("ativos");
  const [orderBy, setOrderBy] = useState<"nome" | "matricula">("nome");
  const [orderDir, setOrderDir] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);

  const debouncedSearch = useDebounced(search);
  useEffect(() => {
    setPage(1);
  }, [debouncedSearch, status, orderBy, orderDir]);

  const params: ServidoresListParams = useMemo(
    () => ({
      search: debouncedSearch,
      ativo: status === "todos" ? undefined : status === "ativos",
      ordering: `${orderDir === "desc" ? "-" : ""}${orderBy}`,
      page,
    }),
    [debouncedSearch, status, orderBy, orderDir, page],
  );

  const { data, isLoading, isError, error, isFetching } = useServidoresList(params);

  const [admissaoOpen, setAdmissaoOpen] = useState(false);

  function ordenarPor(coluna: "nome" | "matricula") {
    if (orderBy === coluna) setOrderDir(orderDir === "asc" ? "desc" : "asc");
    else {
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
            <Users className="h-5 w-5 text-muted-foreground" />
            Servidores
          </h1>
          <p className="text-sm text-muted-foreground">
            Servidores ativos e inativos do município. Clique em uma linha para ver detalhes.
          </p>
        </div>
        <Button onClick={() => setAdmissaoOpen(true)} className="self-start sm:self-auto">
          <Plus className="h-4 w-4 mr-1" />
          Admitir servidor
        </Button>
      </header>

      <div className="flex flex-col sm:flex-row gap-3 sm:items-center">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
          <Input
            type="search"
            placeholder="Buscar por matrícula, nome ou CPF..."
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
              <TableHead className="w-[140px]">
                <button
                  type="button"
                  onClick={() => ordenarPor("matricula")}
                  className="inline-flex items-center gap-1 hover:text-foreground"
                >
                  Matrícula <SortIcon active={orderBy === "matricula"} dir={orderDir} />
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
              <TableHead className="w-[180px]">CPF</TableHead>
              <TableHead className="w-[120px]">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading && <SkeletonRows />}
            {isError && (
              <TableRow>
                <TableCell colSpan={4} className="py-12 text-center text-sm text-destructive">
                  {extractDomainErrorMessage(error) ?? "Falha ao carregar servidores."}
                </TableCell>
              </TableRow>
            )}
            {!isLoading && !isError && data?.results.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} className="py-16 text-center">
                  <div className="flex flex-col items-center gap-3 text-muted-foreground">
                    <Users className="h-8 w-8" />
                    <div>
                      <p className="font-medium text-foreground">Nenhum servidor encontrado.</p>
                      <p className="text-xs mt-1">
                        {debouncedSearch || status !== "ativos"
                          ? "Tente ajustar os filtros."
                          : "Comece admitindo o primeiro servidor."}
                      </p>
                    </div>
                  </div>
                </TableCell>
              </TableRow>
            )}
            {data?.results.map((s) => (
              <TableRow
                key={s.id}
                className="cursor-pointer"
                onClick={() => navigate(`/servidores/${s.id}`)}
              >
                <TableCell className="font-mono text-xs tabular-nums">
                  <Link
                    to={`/servidores/${s.id}`}
                    onClick={(e) => e.stopPropagation()}
                    className="hover:underline"
                  >
                    {s.matricula}
                  </Link>
                </TableCell>
                <TableCell className="font-medium">{s.nome}</TableCell>
                <TableCell className="font-mono text-xs">{formatCpf(s.cpf)}</TableCell>
                <TableCell>
                  {s.ativo ? (
                    <Badge variant="success">Ativo</Badge>
                  ) : (
                    <Badge variant="muted">Inativo</Badge>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {data && data.count > 0 && (
        <footer className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 text-sm text-muted-foreground">
          <span>
            {data.count} servidor{data.count === 1 ? "" : "es"}
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

      <ServidorAdmissaoSheet
        open={admissaoOpen}
        onOpenChange={setAdmissaoOpen}
        onSuccess={(id) => navigate(`/servidores/${id}`)}
      />
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
            <Skeleton className="h-4 w-32" />
          </TableCell>
          <TableCell>
            <Skeleton className="h-5 w-16" />
          </TableCell>
        </TableRow>
      ))}
    </>
  );
}
