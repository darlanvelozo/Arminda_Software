/**
 * Constantes compartilhadas do domínio (espelham os enums do backend).
 *
 * Manter sincronizado com:
 *   - apps.people.models.Regime
 *   - apps.people.models.NaturezaLotacao
 *
 * As variantes de badge são usadas em listagens/dashboard para dar uma cor
 * estável a cada categoria.
 */

import type { BadgeProps } from "@/components/ui/badge";

export const REGIMES = [
  { value: "estatutario", label: "Efetivo", labelLong: "Efetivo (concursado)" },
  { value: "comissionado", label: "Comissionado", labelLong: "Comissionado" },
  {
    value: "temporario",
    label: "Contratado",
    labelLong: "Contratado temporário",
  },
  { value: "eletivo", label: "Eletivo", labelLong: "Eletivo" },
  { value: "estagiario", label: "Estagiário", labelLong: "Estagiário" },
  { value: "celetista", label: "Celetista", labelLong: "Celetista (CLT)" },
] as const;

export type RegimeValue = (typeof REGIMES)[number]["value"];

export const REGIME_VARIANTS: Record<string, NonNullable<BadgeProps["variant"]>> = {
  estatutario: "success",
  comissionado: "warning",
  temporario: "info",
  eletivo: "default",
  estagiario: "muted",
  celetista: "muted",
};

export function regimeLabel(value: string): string {
  return REGIMES.find((r) => r.value === value)?.label ?? value;
}

export const NATUREZAS = [
  { value: "administracao", label: "Administração" },
  { value: "saude", label: "Saúde" },
  { value: "educacao", label: "Educação" },
  { value: "assistencia_social", label: "Assistência social" },
  { value: "outros", label: "Outros" },
] as const;

export type NaturezaValue = (typeof NATUREZAS)[number]["value"];

export const NATUREZA_VARIANTS: Record<string, NonNullable<BadgeProps["variant"]>> = {
  administracao: "muted",
  saude: "info",
  educacao: "success",
  assistencia_social: "warning",
  outros: "outline",
};

export function naturezaLabel(value: string): string {
  return NATUREZAS.find((n) => n.value === value)?.label ?? value;
}
