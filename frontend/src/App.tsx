/**
 * App — roteamento principal (Bloco 1.3).
 *
 * Rotas:
 *   /login                            público
 *   /selecionar-municipio             autenticado, sem AppShell
 *   /                                  autenticado + AppShell + Dashboard
 *   /servidores, /cargos, /lotacoes,
 *   /rubricas, /relatorios            autenticado + AppShell + placeholder
 *   /health, /status                  públicos (legado do Bloco 0)
 *   *                                  404
 */

import { Route, Routes } from "react-router-dom";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import DashboardPage from "@/pages/DashboardPage";
import HealthPage from "@/pages/HealthPage";
import LoginPage from "@/pages/auth/LoginPage";
import SelecionarMunicipioPage from "@/pages/auth/SelecionarMunicipioPage";
import EmConstrucaoPage from "@/pages/EmConstrucaoPage";
import NotFoundPage from "@/pages/NotFoundPage";

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
        <Route index element={<DashboardPage />} />
        <Route path="servidores" element={<EmConstrucaoPage area="Servidores" />} />
        <Route path="cargos" element={<EmConstrucaoPage area="Cargos" />} />
        <Route path="lotacoes" element={<EmConstrucaoPage area="Lotações" />} />
        <Route path="rubricas" element={<EmConstrucaoPage area="Rubricas" />} />
        <Route path="relatorios" element={<EmConstrucaoPage area="Relatórios" />} />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

export default App;
