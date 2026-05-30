/**
 * ConfiguracoesPage — Onda 1.5.
 *
 * Página com 3 abas:
 *   - Perfil — edita nome do próprio usuário
 *   - Segurança — troca de senha
 *   - Usuários — gestão de quem tem acesso ao município (admin only)
 */

import { Landmark, Settings, Shield, UserCircle, Users } from "lucide-react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { PerfilTab } from "./PerfilTab";
import { PrevidenciaTab } from "./PrevidenciaTab";
import { SegurancaTab } from "./SegurancaTab";
import { UsuariosTab } from "./UsuariosTab";

export default function ConfiguracoesPage() {
  return (
    <div className="space-y-6">
      <header className="space-y-1">
        <h1 className="font-semibold inline-flex items-center gap-2" style={{ fontSize: 22 }}>
          <Settings className="h-5 w-5 text-muted-foreground" />
          Configurações
        </h1>
        <p className="text-sm text-muted-foreground">
          Perfil pessoal, segurança, previdência (RPPS) e gestão de usuários do município ativo.
        </p>
      </header>

      <Tabs defaultValue="perfil">
        <TabsList>
          <TabsTrigger value="perfil">
            <UserCircle className="h-4 w-4 mr-1.5" /> Perfil
          </TabsTrigger>
          <TabsTrigger value="seguranca">
            <Shield className="h-4 w-4 mr-1.5" /> Segurança
          </TabsTrigger>
          <TabsTrigger value="previdencia">
            <Landmark className="h-4 w-4 mr-1.5" /> Previdência
          </TabsTrigger>
          <TabsTrigger value="usuarios">
            <Users className="h-4 w-4 mr-1.5" /> Usuários
          </TabsTrigger>
        </TabsList>

        <TabsContent value="perfil">
          <PerfilTab />
        </TabsContent>
        <TabsContent value="seguranca">
          <SegurancaTab />
        </TabsContent>
        <TabsContent value="previdencia">
          <PrevidenciaTab />
        </TabsContent>
        <TabsContent value="usuarios">
          <UsuariosTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
