/**
 * LoginPage — Bloco 1.3 (design Arminda).
 *
 * Layout 2-coluna full-bleed:
 *   - Esquerda: brand panel com gradient + grid decorativo + headline.
 *   - Direita: formulário simples (email + senha) com toggle de senha.
 *
 * Após login:
 *   - 1 município → redireciona para "/"
 *   - 2+ municípios → "/selecionar-municipio"
 */

import { ArrowRight, CheckCircle2, Eye, EyeOff, Lock, Mail, Shield } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { Logo } from "@/components/brand/Logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { extractDomainErrorMessage } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

interface LocationState {
  from?: { pathname?: string };
}

export default function LoginPage() {
  const { isAuthenticated, isLoading, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPwd, setShowPwd] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (isLoading) return null;
  if (isAuthenticated) {
    const state = location.state as LocationState | null;
    return <Navigate to={state?.from?.pathname ?? "/"} replace />;
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErro(null);
    setSubmitting(true);
    try {
      const data = await login({ email, password });
      if (data.user.municipios.length > 1) navigate("/selecionar-municipio");
      else navigate("/");
    } catch (err) {
      setErro(extractDomainErrorMessage(err) ?? "E-mail ou senha invalidos.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen flex bg-background">
      {/* Brand panel — esquerda */}
      <div
        className="hidden lg:flex lg:flex-1 flex-col justify-between relative overflow-hidden text-white"
        style={{
          padding: "40px 48px",
          background: "linear-gradient(135deg, oklch(0.30 0.13 250) 0%, oklch(0.18 0.08 250) 100%)",
        }}
      >
        {/* Grid decorativo */}
        <div
          aria-hidden="true"
          className="absolute inset-0 pointer-events-none"
          style={{
            opacity: 0.06,
            backgroundImage:
              "linear-gradient(white 1px, transparent 1px), linear-gradient(90deg, white 1px, transparent 1px)",
            backgroundSize: "32px 32px",
          }}
        />
        {/* Orb decorativo */}
        <div
          aria-hidden="true"
          className="absolute pointer-events-none"
          style={{
            top: -120,
            right: -120,
            width: 360,
            height: 360,
            borderRadius: "50%",
            background:
              "radial-gradient(circle at center, oklch(0.65 0.18 250 / 0.4), transparent 70%)",
          }}
        />

        <Link to="/" className="relative z-10 inline-flex">
          <Logo light />
        </Link>

        <div className="relative z-10 max-w-lg space-y-4">
          <h1
            className="font-semibold leading-tight"
            style={{ fontSize: 36, letterSpacing: "-0.02em" }}
          >
            Folha de pagamento moderna para a gestão pública.
          </h1>
          <p className="text-sm leading-relaxed opacity-70">
            Cadastros, vínculos, cálculo, exportações eSocial e BI em tempo real — em uma única
            plataforma web.
          </p>
          <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs opacity-90 pt-2">
            <span className="inline-flex items-center gap-1.5">
              <Shield className="h-3.5 w-3.5" /> Conformidade eSocial
            </span>
            <span className="inline-flex items-center gap-1.5">
              <Lock className="h-3.5 w-3.5" /> LGPD-ready
            </span>
            <span className="inline-flex items-center gap-1.5">
              <CheckCircle2 className="h-3.5 w-3.5" /> 99,9% uptime
            </span>
          </div>
        </div>

        <div className="relative z-10 text-xs opacity-60 font-mono">
          v0.3.0-dev · Arminda Software
        </div>
      </div>

      {/* Form panel — direita */}
      <div className="flex-1 flex items-center justify-center px-6 py-10">
        <div className="w-full max-w-sm space-y-7">
          {/* Logo aparece em mobile (esconde brand panel) */}
          <div className="lg:hidden text-center">
            <Logo />
          </div>

          <div className="space-y-1">
            <h2 className="font-semibold" style={{ fontSize: 22, letterSpacing: "-0.015em" }}>
              Entrar
            </h2>
            <p className="text-sm text-muted-foreground">Acesse sua conta para continuar.</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>
            <div className="space-y-1.5">
              <Label htmlFor="email">E-mail institucional</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={submitting}
                  placeholder="seu.nome@municipio.gov.br"
                  className="pl-9"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password">Senha</Label>
                <button type="button" className="text-xs text-primary hover:underline">
                  Esqueci minha senha
                </button>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
                <Input
                  id="password"
                  type={showPwd ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={submitting}
                  placeholder="Sua senha"
                  className="pl-9 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPwd((s) => !s)}
                  className="absolute right-1 top-1/2 -translate-y-1/2 p-2 text-muted-foreground hover:text-foreground rounded-sm"
                  aria-label={showPwd ? "Ocultar senha" : "Mostrar senha"}
                >
                  {showPwd ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {erro && (
              <p className="text-sm text-destructive" role="alert" aria-live="polite">
                {erro}
              </p>
            )}

            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting ? "Autenticando..." : "Continuar"}
              {!submitting && <ArrowRight className="h-4 w-4 ml-1" />}
            </Button>
          </form>

          <div className="border-t pt-5 text-center text-xs text-muted-foreground">
            Problema para acessar? Entre em contato com{" "}
            <a href="mailto:suporte@arminda.app" className="text-primary hover:underline">
              suporte@arminda.app
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
