/**
 * KPIs do Dashboard — contagens agregadas por vínculo e natureza.
 *
 * Estratégia: cada KPI faz uma chamada GET na listagem com filtro
 * e `page_size=1` e lê `count` da resposta paginada. Custa pouco no
 * backend (COUNT query) e dispensa endpoint dedicado.
 *
 * Roda 9 chamadas em paralelo: total + 5 vínculos + 4 naturezas (a
 * "outros" também conta porque é classe legítima).
 */

import { useQueries } from "@tanstack/react-query";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import { NATUREZAS, REGIMES } from "@/lib/constants";

async function countServidoresAtivos(filtros: Record<string, string>): Promise<number> {
  const { data } = await api.get<{ count: number }>("/people/servidores/", {
    params: { ativo: true, page_size: 1, ...filtros },
  });
  return data.count;
}

export interface DashboardKpis {
  totalAtivos: number | undefined;
  porRegime: Record<string, number | undefined>;
  porNatureza: Record<string, number | undefined>;
  isLoading: boolean;
  isError: boolean;
}

export function useDashboardKpis(): DashboardKpis {
  const { activeTenant } = useAuth();

  const queries = useQueries({
    queries: [
      {
        queryKey: ["kpi", "total-ativos", activeTenant],
        queryFn: () => countServidoresAtivos({}),
        enabled: !!activeTenant,
        staleTime: 60_000,
      },
      ...REGIMES.map((r) => ({
        queryKey: ["kpi", "regime", r.value, activeTenant],
        queryFn: () => countServidoresAtivos({ regime: r.value }),
        enabled: !!activeTenant,
        staleTime: 60_000,
      })),
      ...NATUREZAS.map((n) => ({
        queryKey: ["kpi", "natureza", n.value, activeTenant],
        queryFn: () => countServidoresAtivos({ natureza: n.value }),
        enabled: !!activeTenant,
        staleTime: 60_000,
      })),
    ],
  });

  const [totalQ, ...rest] = queries;
  const porRegimeQ = rest.slice(0, REGIMES.length);
  const porNaturezaQ = rest.slice(REGIMES.length);

  const porRegime: Record<string, number | undefined> = {};
  REGIMES.forEach((r, i) => {
    porRegime[r.value] = porRegimeQ[i]?.data;
  });

  const porNatureza: Record<string, number | undefined> = {};
  NATUREZAS.forEach((n, i) => {
    porNatureza[n.value] = porNaturezaQ[i]?.data;
  });

  return {
    totalAtivos: totalQ?.data,
    porRegime,
    porNatureza,
    isLoading: queries.some((q) => q.isLoading),
    isError: queries.some((q) => q.isError),
  };
}
