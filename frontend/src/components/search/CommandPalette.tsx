/**
 * CommandPalette — pesquisa global em ⌘K (Onda 1.5).
 *
 * Comportamento:
 *   - Abre com ⌘K (mac) ou Ctrl+K (Windows/Linux), fecha com Esc.
 *   - Navega entre resultados com ↑/↓; Enter seleciona.
 *   - Busca debounced (250ms) em paralelo nas APIs de cargos, lotações,
 *     servidores e rubricas. Quando vazio, mostra atalhos para as áreas.
 *   - Cada item navega para a rota apropriada e fecha o palette.
 *
 * Não filtra client-side via cmdk (shouldFilter=false) — o backend já
 * filtra por `?search=`.
 */

import { useQuery } from "@tanstack/react-query";
import {
  Briefcase,
  Building2,
  FileText,
  Home,
  Library,
  Map,
  Settings,
  Tag,
  Users,
  Wallet,
} from "lucide-react";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Cargo, Lotacao, Paginated, Rubrica, Servidor } from "@/types";

interface CommandPaletteProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

const ATALHOS = [
  { label: "Dashboard", to: "/", icon: Home },
  { label: "Servidores", to: "/servidores", icon: Users },
  { label: "Cargos", to: "/cargos", icon: Briefcase },
  { label: "Lotações", to: "/lotacoes", icon: Library },
  { label: "Rubricas", to: "/rubricas", icon: Tag },
  { label: "Folha", to: "/folha", icon: Wallet },
  { label: "Relatórios", to: "/relatorios", icon: FileText },
  { label: "Configurações", to: "/configuracoes", icon: Settings },
  { label: "Guia de uso", to: "/guia", icon: Map },
] as const;

interface BuscaResult {
  cargos: Cargo[];
  lotacoes: Lotacao[];
  servidores: Servidor[];
  rubricas: Rubrica[];
}

async function buscarTudo(query: string): Promise<BuscaResult> {
  const params = { search: query, page_size: 5 };
  const [cargos, lotacoes, servidores, rubricas] = await Promise.all([
    api
      .get<Paginated<Cargo>>("/people/cargos/", { params })
      .then((r) => r.data.results)
      .catch(() => [] as Cargo[]),
    api
      .get<Paginated<Lotacao>>("/people/lotacoes/", { params })
      .then((r) => r.data.results)
      .catch(() => [] as Lotacao[]),
    api
      .get<Paginated<Servidor>>("/people/servidores/", { params })
      .then((r) => r.data.results)
      .catch(() => [] as Servidor[]),
    api
      .get<Paginated<Rubrica>>("/payroll/rubricas/", { params })
      .then((r) => r.data.results)
      .catch(() => [] as Rubrica[]),
  ]);
  return { cargos, lotacoes, servidores, rubricas };
}

function useDebounced<T>(value: T, delayMs = 250): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(t);
  }, [value, delayMs]);
  return debounced;
}

export function CommandPalette({ open, onOpenChange }: CommandPaletteProps) {
  const { activeTenant } = useAuth();
  const navigate = useNavigate();

  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounced(query);
  const hasQuery = debouncedQuery.trim().length >= 2;

  useEffect(() => {
    if (!open) setQuery("");
  }, [open]);

  const { data, isFetching } = useQuery({
    queryKey: ["palette-search", activeTenant, debouncedQuery],
    queryFn: () => buscarTudo(debouncedQuery.trim()),
    enabled: open && hasQuery && !!activeTenant,
    staleTime: 30_000,
  });

  function go(to: string) {
    onOpenChange(false);
    navigate(to);
  }

  return (
    <CommandDialog open={open} onOpenChange={onOpenChange} shouldFilter={false}>
      <CommandInput
        placeholder="Buscar servidor, cargo, lotação, rubrica…"
        value={query}
        onValueChange={setQuery}
      />
      <CommandList>
        {!hasQuery && (
          <CommandGroup heading="Atalhos">
            {ATALHOS.map(({ label, to, icon: Icon }) => (
              <CommandItem key={to} onSelect={() => go(to)} value={`atalho-${label}`}>
                <Icon className="h-4 w-4 mr-2 text-muted-foreground" />
                {label}
              </CommandItem>
            ))}
          </CommandGroup>
        )}

        {hasQuery && (
          <>
            {isFetching && (
              <div className="py-4 text-center text-xs text-muted-foreground">
                Buscando…
              </div>
            )}

            {!isFetching &&
              data &&
              data.cargos.length === 0 &&
              data.lotacoes.length === 0 &&
              data.servidores.length === 0 &&
              data.rubricas.length === 0 && (
                <CommandEmpty>Nada encontrado para "{debouncedQuery}".</CommandEmpty>
              )}

            {data && data.servidores.length > 0 && (
              <CommandGroup heading="Servidores">
                {data.servidores.map((s) => (
                  <CommandItem
                    key={`s-${s.id}`}
                    onSelect={() => go(`/servidores/${s.id}`)}
                    value={`servidor-${s.id}-${s.nome}`}
                  >
                    <Users className="h-4 w-4 mr-2 text-muted-foreground" />
                    <span className="flex-1 truncate">{s.nome}</span>
                    <span className="text-xs text-muted-foreground font-mono">
                      Mat. {s.matricula}
                    </span>
                  </CommandItem>
                ))}
              </CommandGroup>
            )}

            {data && data.cargos.length > 0 && (
              <>
                <CommandSeparator />
                <CommandGroup heading="Cargos">
                  {data.cargos.map((c) => (
                    <CommandItem
                      key={`c-${c.id}`}
                      onSelect={() => go("/cargos")}
                      value={`cargo-${c.id}-${c.nome}`}
                    >
                      <Briefcase className="h-4 w-4 mr-2 text-muted-foreground" />
                      <span className="flex-1 truncate">{c.nome}</span>
                      <span className="text-xs text-muted-foreground font-mono">
                        {c.codigo}
                      </span>
                    </CommandItem>
                  ))}
                </CommandGroup>
              </>
            )}

            {data && data.lotacoes.length > 0 && (
              <>
                <CommandSeparator />
                <CommandGroup heading="Lotações">
                  {data.lotacoes.map((l) => (
                    <CommandItem
                      key={`l-${l.id}`}
                      onSelect={() => go("/lotacoes")}
                      value={`lotacao-${l.id}-${l.nome}`}
                    >
                      <Building2 className="h-4 w-4 mr-2 text-muted-foreground" />
                      <span className="flex-1 truncate">{l.nome}</span>
                      <span className="text-xs text-muted-foreground font-mono">
                        {l.sigla || l.codigo}
                      </span>
                    </CommandItem>
                  ))}
                </CommandGroup>
              </>
            )}

            {data && data.rubricas.length > 0 && (
              <>
                <CommandSeparator />
                <CommandGroup heading="Rubricas">
                  {data.rubricas.map((r) => (
                    <CommandItem
                      key={`r-${r.id}`}
                      onSelect={() => go("/rubricas")}
                      value={`rubrica-${r.id}-${r.nome}`}
                    >
                      <Tag className="h-4 w-4 mr-2 text-muted-foreground" />
                      <span className="flex-1 truncate">{r.nome}</span>
                      <span className="text-xs text-muted-foreground font-mono">
                        {r.codigo}
                      </span>
                    </CommandItem>
                  ))}
                </CommandGroup>
              </>
            )}
          </>
        )}
      </CommandList>
    </CommandDialog>
  );
}

/**
 * Hook: registra ⌘K / Ctrl+K para abrir o palette globalmente.
 */
export function useCommandPaletteShortcut(onOpen: () => void) {
  useEffect(() => {
    function handler(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        onOpen();
      }
    }
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onOpen]);
}
