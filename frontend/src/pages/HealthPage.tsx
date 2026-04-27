import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";

interface CheckDetail {
  status: string;
  detail: string;
}

interface StatusResponse {
  status: string;
  service: string;
  version: string;
  uptime: string;
  uptime_seconds: number;
  checks: Record<string, CheckDetail>;
}

interface HealthResponse {
  status: string;
  service: string;
}

async function fetchStatus(): Promise<StatusResponse> {
  const baseURL = import.meta.env.VITE_API_URL?.replace("/api", "") || "";
  const response = await api.get<StatusResponse>("/status/", { baseURL });
  return response.data;
}

async function fetchHealth(): Promise<HealthResponse> {
  const baseURL = import.meta.env.VITE_API_URL?.replace("/api", "") || "";
  const response = await api.get<HealthResponse>("/health/", { baseURL });
  return response.data;
}

function StatusBadge({ status }: { status: string }) {
  const isOk = status === "ok";
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ${
        isOk
          ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
          : "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400"
      }`}
    >
      <span
        className={`h-2 w-2 rounded-full ${isOk ? "bg-green-500" : "bg-red-500"}`}
      />
      {isOk ? "Operacional" : "Com problemas"}
    </span>
  );
}

function HealthPage() {
  const statusQuery = useQuery({
    queryKey: ["status"],
    queryFn: fetchStatus,
    retry: 1,
    refetchInterval: 30_000,
  });

  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    retry: 1,
    refetchInterval: 30_000,
  });

  const isLoading = statusQuery.isLoading || healthQuery.isLoading;
  const hasError = statusQuery.isError && healthQuery.isError;

  return (
    <main className="min-h-screen flex flex-col items-center px-6 py-12">
      <div className="max-w-lg w-full space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold">Status do Sistema</h1>
          <p className="text-sm text-muted-foreground">
            Arminda &mdash; Folha de pagamento e gestao de pessoal
          </p>
        </div>

        {/* Overall status */}
        <div className="rounded-lg border bg-card p-6 text-center space-y-3">
          {isLoading && (
            <div className="flex items-center justify-center gap-2">
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-primary border-t-transparent" />
              <span className="text-sm text-muted-foreground">
                Verificando servicos...
              </span>
            </div>
          )}

          {hasError && (
            <div className="space-y-2">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-red-100 px-3 py-1 text-xs font-semibold text-red-800 dark:bg-red-900/30 dark:text-red-400">
                <span className="h-2 w-2 rounded-full bg-red-500" />
                Fora do ar
              </span>
              <p className="text-sm text-muted-foreground">
                Nao foi possivel conectar ao backend.
              </p>
              <p className="text-xs text-muted-foreground">
                Verifique se o servidor esta rodando em{" "}
                <code className="rounded bg-muted px-1 py-0.5">
                  http://localhost:8000
                </code>
              </p>
            </div>
          )}

          {statusQuery.data && (
            <div className="space-y-1">
              <StatusBadge status={statusQuery.data.status} />
              <p className="text-xs text-muted-foreground pt-1">
                v{statusQuery.data.version} &middot; Uptime:{" "}
                {statusQuery.data.uptime}
              </p>
            </div>
          )}
        </div>

        {/* Service checks */}
        {statusQuery.data && (
          <div className="rounded-lg border bg-card divide-y">
            <div className="px-6 py-3">
              <h2 className="text-sm font-semibold">Servicos</h2>
            </div>

            {/* API check (from /health/) */}
            <div className="flex items-center justify-between px-6 py-4">
              <div className="flex items-center gap-3">
                <span className="flex h-8 w-8 items-center justify-center rounded-md bg-muted text-sm">
                  API
                </span>
                <div>
                  <p className="text-sm font-medium">API REST</p>
                  <p className="text-xs text-muted-foreground">
                    Django REST Framework
                  </p>
                </div>
              </div>
              <StatusBadge
                status={healthQuery.data ? "ok" : "error"}
              />
            </div>

            {/* Dynamic checks from /status/ */}
            {Object.entries(statusQuery.data.checks).map(
              ([name, check]) => (
                <div
                  key={name}
                  className="flex items-center justify-between px-6 py-4"
                >
                  <div className="flex items-center gap-3">
                    <span className="flex h-8 w-8 items-center justify-center rounded-md bg-muted text-sm">
                      DB
                    </span>
                    <div>
                      <p className="text-sm font-medium capitalize">
                        {name === "database" ? "Banco de Dados" : name}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {check.detail}
                      </p>
                    </div>
                  </div>
                  <StatusBadge status={check.status} />
                </div>
              ),
            )}
          </div>
        )}

        {/* Raw JSON (collapsible) */}
        {statusQuery.data && (
          <details className="rounded-lg border bg-card">
            <summary className="px-6 py-3 text-sm font-semibold cursor-pointer hover:bg-muted/50 transition-colors">
              Resposta JSON
            </summary>
            <pre className="px-6 pb-4 text-xs overflow-auto text-muted-foreground">
              {JSON.stringify(statusQuery.data, null, 2)}
            </pre>
          </details>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <Link to="/" className="text-primary hover:underline">
            &larr; Voltar
          </Link>
          <span className="text-xs">
            Atualiza a cada 30s
          </span>
        </div>
      </div>
    </main>
  );
}

export default HealthPage;
