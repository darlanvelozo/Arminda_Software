/**
 * Logo Arminda — adaptado do bundle de design.
 *
 * SVG com retângulo arredondado (cor primária) + monograma "M" estilizado
 * formado por dois traços + linha mediana. Texto "Arminda" ao lado.
 *
 * Variant `light` inverte cores para uso em fundos escuros (login brand panel).
 */

import { cn } from "@/lib/utils";

interface LogoProps {
  light?: boolean;
  size?: "sm" | "md" | "lg";
  className?: string;
  withText?: boolean;
}

const SIZE_TABLE = {
  sm: { font: 16, icon: 22 },
  md: { font: 18, icon: 26 },
  lg: { font: 24, icon: 32 },
};

export function Logo({ light = false, size = "md", className, withText = true }: LogoProps) {
  const { font, icon } = SIZE_TABLE[size];

  // Em fundo escuro: branco (rect) + azul (path).
  // Em fundo padrão: primary (rect) + primary-foreground (path).
  const rectFill = light ? "white" : "oklch(var(--primary))";
  const stroke = light ? "oklch(0.30 0.13 250)" : "oklch(var(--primary-foreground))";

  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <svg width={icon} height={icon} viewBox="0 0 32 32" fill="none" aria-hidden="true">
        <rect width="32" height="32" rx="7" fill={rectFill} />
        <path
          d="M9 22 L13 10 L19 10 L23 22"
          stroke={stroke}
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
          fill="none"
        />
        <line
          x1="11"
          y1="17"
          x2="21"
          y2="17"
          stroke={stroke}
          strokeWidth="2.4"
          strokeLinecap="round"
        />
      </svg>
      {withText && (
        <span
          style={{
            fontSize: font,
            fontWeight: 600,
            letterSpacing: "-0.01em",
            color: light ? "white" : "oklch(var(--foreground))",
          }}
        >
          Arminda
        </span>
      )}
    </span>
  );
}
