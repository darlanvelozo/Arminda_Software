/**
 * App — roteamento principal (Bloco 1.3c).
 *
 * Rotas autenticadas usam React.lazy para code-splitting por rota; assim o
 * bundle inicial só carrega o necessário para login + dashboard. As páginas
 * de domínio (cargos, lotações, rubricas, servidores) viram chunks separados.
 *
 * Rotas:
 *   /login                            público
 *   /selecionar-municipio             autenticado, sem AppShell
 *   /                                  autenticado + AppShell + Dashboard
 *   /servidores, /servidores/:id, /cargos, /lotacoes, /rubricas
 *                                      autenticado + AppShell + páginas reais
 *   /folha, /relatorios, /configuracoes
 *                                      autenticado + AppShell + placeholder
 *                                      (telas reais entram em Bloco 2/4/futuras ondas)
 *   /health, /status                  públicos (legado do Bloco 0)
 *   *                                  404
 */

import { lazy, Suspense } from "react";
import { Route, Routes } from "react-router-dom";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Skeleton } from "@/components/ui/skeleton";
import HealthPage from "@/pages/HealthPage";
import LoginPage from "@/pages/auth/LoginPage";
import SelecionarMunicipioPage from "@/pages/auth/SelecionarMunicipioPage";
import EmConstrucaoPage from "@/pages/EmConstrucaoPage";
import NotFoundPage from "@/pages/NotFoundPage";

// Code-split: páginas de domínio só carregam quando o usuário navega até elas.
const DashboardPage = lazy(() => import("@/pages/DashboardPage"));
const CargosListPage = lazy(() => import("@/pages/cargos/CargosListPage"));
const LotacoesListPage = lazy(() => import("@/pages/lotacoes/LotacoesListPage"));
const RubricasListPage = lazy(() => import("@/pages/rubricas/RubricasListPage"));
const ServidoresListPage = lazy(() => import("@/pages/servidores/ServidoresListPage"));
const ServidorDetailPage = lazy(() => import("@/pages/servidores/ServidorDetailPage"));

function PageFallback() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-48" />
      <Skeleton className="h-4 w-72" />
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
    </div>
  );
}

function lazyRoute(node: React.ReactNode) {
  return <Suspense fallback={<PageFallback />}>{node}</Suspense>;
}

function App() {
  return (
    <Routes>
      {/* Públicas */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/health" element={<HealthPage />} />
      <Route path="/status" element={<HealthPage />} />

      {/* Autenticadas, sem AppShell */}
      <Route
        path="/selecionar-municipio"
        element={
          <RequireAuth>
            <SelecionarMunicipioPage />
          </RequireAuth>
        }
      />

      {/* Autenticadas com AppShell */}
      <Route
        path="/"
        element={
          <RequireAuth>
            <AppShell />
          </RequireAuth>
        }
      >
        <Route index element={lazyRoute(<DashboardPage />)} />
        <Route path="servidores" element={lazyRoute(<ServidoresListPage />)} />
        <Route path="servidores/:id" element={lazyRoute(<ServidorDetailPage />)} />
        <Route path="cargos" element={lazyRoute(<CargosListPage />)} />
        <Route path="lotacoes" element={lazyRoute(<LotacoesListPage />)} />
        <Route path="folha" element={<EmConstrucaoPage area="Folha de Pagamento" />} />
        <Route path="rubricas" element={lazyRoute(<RubricasListPage />)} />
        <Route path="relatorios" element={<EmConstrucaoPage area="Relatórios" />} />
        <Route path="configuracoes" element={<EmConstrucaoPage area="Configurações" />} />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

export default App;
