/**
 * LoginPage (Bloco 1.3).
 *
 * POST /api/auth/login/ → tokens + user. Após sucesso:
 *   - Se user tem 1 município: redireciona para /
 *   - Se user tem 2+: redireciona para /selecionar-municipio
 *   - Se 0 (apenas staff_arminda sem papel): vai pra / mesmo (admin global)
 */

import { useState, type FormEvent } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth-context";
import { extractDomainErrorMessage } from "@/lib/api";

interface LocationState {
  from?: { pathname?: string };
}

export default function LoginPage() {
  const { isAuthenticated, isLoading, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (isLoading) {
    return null;
  }

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
      // Decide rota pos-login
      if (data.user.municipios.length > 1) {
        navigate("/selecionar-municipio");
      } else {
        navigate("/");
      }
    } catch (err) {
      setErro(extractDomainErrorMessage(err) ?? "E-mail ou senha invalidos.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="min-h-screen grid place-items-center bg-muted/30 px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center space-y-1">
          <Link to="/" className="text-3xl font-bold tracking-tight text-primary">
            Arminda
          </Link>
          <p className="text-sm text-muted-foreground">Folha de pagamento e gestão de pessoal</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Entrar</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4" noValidate>
              <div className="space-y-2">
                <Label htmlFor="email">E-mail</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={submitting}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Senha</Label>
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={submitting}
                />
              </div>

              {erro && (
                <p className="text-sm text-destructive" role="alert" aria-live="polite">
                  {erro}
                </p>
              )}

              <Button type="submit" className="w-full" disabled={submitting}>
                {submitting ? "Entrando..." : "Entrar"}
              </Button>
            </form>
          </CardContent>
        </Card>

        <p className="text-center text-xs text-muted-foreground">
          Em caso de problemas, contate o administrador do município.
        </p>
      </div>
    </main>
  );
}
