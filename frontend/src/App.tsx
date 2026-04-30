/**
 * App — roteamento principal (Bloco 1.3).
 *
 * Rotas:
 *   /login                            público
 *   /selecionar-municipio             autenticado, sem AppShell
 *   /                                  autenticado + AppShell + Dashboard
 *   /servidores, /cargos, /lotacoes,
 *   /folha, /rubricas, /relatorios,
 *   /configuracoes                    autenticado + AppShell + placeholder
 *                                     (telas reais entram na Onda 1.3b/Bloco 2)
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
import CargosListPage from "@/pages/cargos/CargosListPage";
import LotacoesListPage from "@/pages/lotacoes/LotacoesListPage";
import RubricasListPage from "@/pages/rubricas/RubricasListPage";
import ServidorDetailPage from "@/pages/servidores/ServidorDetailPage";
import ServidoresListPage from "@/pages/servidores/ServidoresListPage";
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
        <Route path="servidores" element={<ServidoresListPage />} />
        <Route path="servidores/:id" element={<ServidorDetailPage />} />
        <Route path="cargos" element={<CargosListPage />} />
        <Route path="lotacoes" element={<LotacoesListPage />} />
        <Route path="folha" element={<EmConstrucaoPage area="Folha de Pagamento" />} />
        <Route path="rubricas" element={<RubricasListPage />} />
        <Route path="relatorios" element={<EmConstrucaoPage area="Relatórios" />} />
        <Route path="configuracoes" element={<EmConstrucaoPage area="Configurações" />} />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}

export default App;
