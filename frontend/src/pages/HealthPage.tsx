import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { api } from "@/lib/api";

interface HealthResponse {
  status: string;
  service: string;
}

async function fetchHealth(): Promise<HealthResponse> {
  // O endpoint /health/ está fora do prefixo /api/, então usamos baseURL absoluto
  const response = await api.get<HealthResponse>("/health/", {
    baseURL: import.meta.env.VITE_API_URL?.replace("/api", "") || "",
  });
  return response.data;
}

function HealthPage() {
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    retry: 1,
  });

  return (
    <main className="min-h-screen flex flex-col items-center justify-center px-6 py-12">
      <div className="max-w-md w-full space-y-6">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-bold">Status do sistema</h1>
          <p className="text-sm text-muted-foreground">
            Verificação de conectividade com a API
          </p>
        </div>

        <div className="rounded-lg border bg-card p-6 space-y-3">
          {isLoading && (
            <p className="text-sm text-muted-foreground">Verificando…</p>
          )}

          {isError && (
            <div className="space-y-2">
              <p className="text-sm font-medium text-destructive">
                Não foi possível conectar à API.
              </p>
              <p className="text-xs text-muted-foreground">
                {error instanceof Error ? error.message : "Erro desconhecido"}
              </p>
              <p className="text-xs text-muted-foreground">
                Confira se o backend está rodando em{" "}
                <code className="rounded bg-muted px-1 py-0.5">
                  http://localhost:8000
                </code>
                .
              </p>
            </div>
          )}

          {data && (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-green-500" />
                <span className="text-sm font-medium">API operacional</span>
              </div>
              <pre className="text-xs bg-muted rounded p-3 overflow-auto">
                {JSON.stringify(data, null, 2)}
              </pre>
            </div>
          )}
        </div>

        <div className="text-center">
          <Link
            to="/"
            className="text-sm text-primary hover:underline"
          >
            ← Voltar
          </Link>
        </div>
      </div>
    </main>
  );
}

export default HealthPage;
