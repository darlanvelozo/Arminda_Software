/**
 * Hooks TanStack Query para OrgaoEmissor + Sindicato (Onda 1.6a).
 *
 * Versão mínima — apenas listagem para popular dropdowns do bulk-edit
 * (Onda 1.6b). CRUD completo é exposto via admin Django até o frontend
 * dedicado existir.
 */

import { useQuery } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { OrgaoEmissor, Paginated, Sindicato } from "@/types";

const ORGAOS_BASE = "/people/orgaos-emissores/";
const SINDICATOS_BASE = "/people/sindicatos/";

async function fetchOrgaos(): Promise<Paginated<OrgaoEmissor>> {
  const { data } = await api.get<Paginated<OrgaoEmissor>>(ORGAOS_BASE, {
    params: { page_size: 100, ordering: "nome" },
  });
  return data;
}

async function fetchSindicatos(): Promise<Paginated<Sindicato>> {
  const { data } = await api.get<Paginated<Sindicato>>(SINDICATOS_BASE, {
    params: { page_size: 100, ordering: "nome" },
  });
  return data;
}

export function useOrgaosEmissoresList() {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: ["orgaos-emissores", activeTenant, "list"] as const,
    queryFn: fetchOrgaos,
    enabled: !!activeTenant,
  });
}

export function useSindicatosList() {
  const { activeTenant } = useAuth();
  return useQuery({
    queryKey: ["sindicatos", activeTenant, "list"] as const,
    queryFn: fetchSindicatos,
    enabled: !!activeTenant,
  });
}
