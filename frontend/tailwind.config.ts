import type { Config } from "tailwindcss";

/**
 * Tailwind config — Bloco 1.3 (alinhado ao design Arminda).
 *
 * Mudanças vs Bloco 0:
 *   - Cores em OKLCH (em vez de HSL).
 *   - Tokens estendidos: primary-soft, success, warning, info, border-strong.
 *   - radius nominal 0.5rem (8px) — compatível com shadcn.
 *   - Fonts mapeadas para Inter (sans) e JetBrains Mono (mono).
 *
 * Convenção: as variáveis CSS guardam APENAS os componentes oklch
 * (`L C H`), e este config envelopa em `oklch(...)` ao consumir.
 * Isso permite usar `oklch(var(--primary) / 0.4)` para alfa.
 */
const oklch = (token: string) => `oklch(var(--${token}))`;

const config: Config = {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: { "2xl": "1400px" },
    },
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      colors: {
        border: oklch("border"),
        "border-strong": oklch("border-strong"),
        input: oklch("input"),
        ring: oklch("ring"),
        background: oklch("background"),
        foreground: oklch("foreground"),
        primary: {
          DEFAULT: oklch("primary"),
          foreground: oklch("primary-foreground"),
          soft: oklch("primary-soft"),
          "soft-foreground": oklch("primary-soft-foreground"),
        },
        secondary: {
          DEFAULT: oklch("secondary"),
          foreground: oklch("secondary-foreground"),
        },
        destructive: {
          DEFAULT: oklch("destructive"),
          foreground: oklch("destructive-foreground"),
          soft: oklch("destructive-soft"),
          "soft-foreground": oklch("destructive-soft-foreground"),
        },
        muted: {
          DEFAULT: oklch("muted"),
          foreground: oklch("muted-foreground"),
        },
        accent: {
          DEFAULT: oklch("accent"),
          foreground: oklch("accent-foreground"),
        },
        card: {
          DEFAULT: oklch("card"),
          foreground: oklch("card-foreground"),
        },
        popover: {
          DEFAULT: oklch("popover"),
          foreground: oklch("popover-foreground"),
        },
        success: {
          DEFAULT: oklch("success"),
          foreground: oklch("success-foreground"),
          soft: oklch("success-soft"),
          "soft-foreground": oklch("success-soft-foreground"),
        },
        warning: {
          DEFAULT: oklch("warning"),
          foreground: oklch("warning-foreground"),
          soft: oklch("warning-soft"),
          "soft-foreground": oklch("warning-soft-foreground"),
        },
        info: {
          DEFAULT: oklch("info"),
          foreground: oklch("info-foreground"),
          soft: oklch("info-soft"),
          "soft-foreground": oklch("info-soft-foreground"),
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "slide-up": {
          from: { transform: "translateY(8px)", opacity: "0" },
          to: { transform: "translateY(0)", opacity: "1" },
        },
        "slide-from-right": {
          from: { transform: "translateX(100%)" },
          to: { transform: "translateX(0)" },
        },
      },
      animation: {
        "fade-in": "fade-in 0.15s ease",
        "slide-up": "slide-up 0.18s ease",
        "slide-from-right": "slide-from-right 0.2s ease",
      },
    },
  },
  plugins: [],
};

export default config;
