/**
 * GuiaPage — Guia de uso vivo do Arminda.
 *
 * É a documentação visível do sistema dentro do próprio sistema. Atualizar
 * SEMPRE que uma onda entregar funcionalidade nova ou mudar permissão.
 *
 * Convenções:
 *   - Cada feature tem um <StatusBadge> indicando se está disponível,
 *     em construção, ou só no roadmap futuro.
 *   - LAST_UPDATED muda toda vez que o conteúdo é tocado.
 *   - Seções têm `id` para deep-link via URL hash (#papeis, #servidores...).
 *
 * Não substitui o `docs/` (ADRs, ROADMAP, ARCHITECTURE) — aqui é manual de
 * uso para operadores; lá é decisão técnica para devs.
 */

import {
  AlertCircle,
  Briefcase,
  Building2,
  CheckCircle2,
  Construction,
  ExternalLink,
  FileText,
  Info,
  Keyboard,
  Library,
  Lightbulb,
  ListChecks,
  Lock,
  Map,
  RotateCw,
  Settings as SettingsIcon,
  Shield,
  Tag,
  Upload,
  Users,
  Wallet,
} from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

const LAST_UPDATED = "2026-07-10";

interface TocItem {
  id: string;
  label: string;
  icon: typeof Info;
}

const TOC: TocItem[] = [
  { id: "visao-geral", label: "Visão geral", icon: Info },
  { id: "como-comecar", label: "Como começar", icon: ListChecks },
  { id: "municipio", label: "Município ativo", icon: Building2 },
  { id: "papeis", label: "Papéis e permissões", icon: Shield },
  { id: "organizacao", label: "Organização: vínculos e áreas", icon: Library },
  { id: "cadastros", label: "Cadastros centrais", icon: Briefcase },
  { id: "servidores", label: "Servidores", icon: Users },
  { id: "configuracoes", label: "Configurações", icon: SettingsIcon },
  { id: "atalhos", label: "Pesquisa e atalhos", icon: Keyboard },
  { id: "folha", label: "Folha de pagamento", icon: Wallet },
  { id: "importador", label: "Importador Fiorilli SIP", icon: Upload },
  { id: "em-construcao", label: "Em construção", icon: Construction },
  { id: "suporte", label: "Suporte", icon: Lightbulb },
];

export default function GuiaPage() {
  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h1 className="font-semibold inline-flex items-center gap-2" style={{ fontSize: 22 }}>
          <Map className="h-5 w-5 text-muted-foreground" />
          Guia de uso
        </h1>
        <p className="text-sm text-muted-foreground">
          O que está pronto, o que está em construção, e como navegar pelo Arminda. Esta
          página é atualizada a cada entrega — é a documentação viva do sistema.
        </p>
        <p className="text-xs text-muted-foreground">
          Última atualização: <strong>{formatDate(LAST_UPDATED)}</strong> · Estado:
          <span className="ml-1 inline-flex items-center gap-2">
            <Badge variant="success">Blocos 0–1 · Bloco 2 (folha) · Bloco 3 (folhas especiais) ✓</Badge>
            <Badge variant="info">Bloco 4 em andamento — eSocial (geração, XSD, cofre + assinatura) ✓ (v0.21.0)</Badge>
          </span>
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[220px_1fr]">
        <aside className="hidden lg:block">
          <nav
            aria-label="Sumário"
            className="sticky top-4 space-y-1 text-sm"
          >
            <div className="text-[11px] uppercase tracking-wider font-medium text-muted-foreground mb-2 px-2">
              Sumário
            </div>
            {TOC.map(({ id, label, icon: Icon }) => (
              <a
                key={id}
                href={`#${id}`}
                className="flex items-center gap-2 px-2 py-1.5 rounded-md text-muted-foreground hover:bg-accent hover:text-foreground transition-colors"
              >
                <Icon className="h-3.5 w-3.5 shrink-0" />
                <span className="truncate">{label}</span>
              </a>
            ))}
          </nav>
        </aside>

        <article className="space-y-10 max-w-3xl">
          <SectionVisaoGeral />
          <SectionComoComecar />
          <SectionMunicipio />
          <SectionPapeis />
          <SectionOrganizacao />
          <SectionCadastros />
          <SectionServidores />
          <SectionConfiguracoes />
          <SectionAtalhos />
          <SectionFolha />
          <SectionImportador />
          <SectionEmConstrucao />
          <SectionSuporte />
        </article>
      </div>
    </div>
  );
}

// ============================================================
// Seções
// ============================================================

function SectionVisaoGeral() {
  return (
    <Section id="visao-geral" icon={Info} title="Visão geral">
      <p>
        O <strong>Arminda</strong> é um sistema multi-tenant de folha de pagamento e gestão
        de pessoal para prefeituras brasileiras. Substitui sistemas legados (como o
        Fiorilli SIP) com paridade funcional e diferenciação em UX, mobile e BI.
      </p>
      <p>
        O sistema é construído por blocos com critérios objetivos de aceitação. Esta
        página acompanha a evolução: você sempre vê aqui o que já dá para usar, o que está
        sendo construído, e o que ainda virá.
      </p>
      <Callout variant="info">
        Cliente-alvo: prefeituras de pequeno e médio porte (até ~16 mil servidores).
        Piloto previsto em município no Maranhão (Janeiro/2027).
      </Callout>
    </Section>
  );
}

function SectionComoComecar() {
  return (
    <Section id="como-comecar" icon={ListChecks} title="Como começar">
      <ol className="list-decimal pl-5 space-y-2">
        <li>
          Acesse a tela de login com seu e-mail institucional e senha.
          <Status status="ok" />
        </li>
        <li>
          Se você opera em mais de um município, escolha qual deles é o ativo na próxima
          tela. Pode trocar a qualquer momento pelo cabeçalho da sidebar.
          <Status status="ok" />
        </li>
        <li>
          O <strong>Dashboard</strong> mostra atalhos para as áreas operacionais e cards
          de KPI (alguns ainda em <em>placeholder</em> — entram quando o cálculo de folha
          chegar no Bloco 2).
          <Status status="parcial" />
        </li>
      </ol>
      <Callout variant="tip">
        Se você foi cadastrado por um administrador com senha temporária, troque-a em{" "}
        <Link to="/configuracoes" className="underline">Configurações → Segurança</Link>{" "}
        no primeiro acesso.
      </Callout>
    </Section>
  );
}

function SectionMunicipio() {
  return (
    <Section id="municipio" icon={Building2} title="Município ativo (multi-tenant)">
      <p>
        Cada município opera em um <strong>schema isolado do PostgreSQL</strong>. Isso
        significa que os dados de um município nunca cruzam com os de outro, mesmo que o
        usuário tenha acesso aos dois.
      </p>
      <ul className="list-disc pl-5 space-y-1.5">
        <li>
          O <strong>município ativo</strong> aparece no card da sidebar.
        </li>
        <li>
          Para trocar, clique no ícone <RotateCw className="inline h-3.5 w-3.5 align-text-bottom" />{" "}
          ao lado do nome (só aparece se você tiver acesso a mais de um) — você é levado
          para a tela <Link to="/selecionar-municipio" className="underline">selecionar
          município</Link>.
        </li>
        <li>
          Toda chamada à API leva o cabeçalho <code className="text-xs bg-muted px-1 rounded">X-Tenant</code>{" "}
          com o schema do município ativo. O frontend faz isso automaticamente.
        </li>
      </ul>
      <Callout variant="warning">
        Não é possível ter operações cruzadas (ex.: transferir um servidor de um município
        para outro). Isso é proposital — cada prefeitura é uma entidade jurídica
        independente.
      </Callout>
    </Section>
  );
}

function SectionPapeis() {
  return (
    <Section id="papeis" icon={Shield} title="Papéis e permissões (RBAC)">
      <p>
        O acesso é controlado por <strong>papéis por município</strong>. Um mesmo usuário
        pode ter papéis diferentes em municípios diferentes.
      </p>
      <Card>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/40 text-xs uppercase tracking-wider">
                <tr>
                  <th className="text-left py-2 px-3 font-medium">Papel</th>
                  <th className="text-left py-2 px-3 font-medium">Pode</th>
                  <th className="text-left py-2 px-3 font-medium">Não pode</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                <tr>
                  <td className="py-3 px-3 font-medium">staff_arminda</td>
                  <td className="py-3 px-3">Atravessar todos os tenants para suporte técnico.</td>
                  <td className="py-3 px-3 text-muted-foreground">—</td>
                </tr>
                <tr>
                  <td className="py-3 px-3 font-medium">admin_municipio</td>
                  <td className="py-3 px-3">
                    Tudo no município ativo: cadastros, admissões, desligamentos,
                    importação, configurações.
                  </td>
                  <td className="py-3 px-3 text-muted-foreground">Acessar outros municípios.</td>
                </tr>
                <tr>
                  <td className="py-3 px-3 font-medium">rh_municipio</td>
                  <td className="py-3 px-3">
                    Gerir servidores e vínculos: admitir, desligar, transferir, editar
                    dados, cadastrar dependentes.
                  </td>
                  <td className="py-3 px-3 text-muted-foreground">
                    Configurar usuários ou alterar permissões.
                  </td>
                </tr>
                <tr>
                  <td className="py-3 px-3 font-medium">financeiro_municipio</td>
                  <td className="py-3 px-3">
                    Tudo de RH + ações de folha (Bloco 2): fechar competência, lançamentos
                    eventuais, gerar holerites.
                  </td>
                  <td className="py-3 px-3 text-muted-foreground">
                    Configurar usuários ou alterar permissões.
                  </td>
                </tr>
                <tr>
                  <td className="py-3 px-3 font-medium">leitura_municipio</td>
                  <td className="py-3 px-3">
                    Visualizar tudo no município (servidores, folha, relatórios).
                  </td>
                  <td className="py-3 px-3 text-muted-foreground">
                    Qualquer escrita (criar, editar, excluir).
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
      <Callout variant="info">
        Toda alteração feita por um usuário fica registrada no histórico
        (<code className="text-xs bg-muted px-1 rounded">simple-history</code>) — quem
        mudou, quando mudou, e o que estava antes.
      </Callout>
    </Section>
  );
}

function SectionOrganizacao() {
  return (
    <Section
      id="organizacao"
      icon={Library}
      title="Organização: vínculos e áreas (secretarias)"
    >
      <p>
        Os servidores são organizados em duas dimensões independentes que
        combinam livremente. Isso resolve o problema clássico do sistema
        legado em que "todo mundo aparece numa única lotação".
      </p>

      <h3 className="text-base font-semibold mt-4">Por vínculo (contrato)</h3>
      <p>
        Cada vínculo tem um regime próprio. O mesmo servidor pode ter dois
        vínculos com regimes diferentes (raro, mas existe em prefeituras
        pequenas onde o concursado também ocupa cargo comissionado).
      </p>
      <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 pl-0 list-none">
        <li className="rounded-md border p-3">
          <strong>Efetivos</strong>
          <p className="text-xs text-muted-foreground mt-1">
            Concursados estatutários. Regime jurídico próprio da prefeitura.
          </p>
        </li>
        <li className="rounded-md border p-3">
          <strong>Comissionados</strong>
          <p className="text-xs text-muted-foreground mt-1">
            Cargo de confiança, nomeação por ato do Prefeito.
          </p>
        </li>
        <li className="rounded-md border p-3">
          <strong>Contratados</strong>
          <p className="text-xs text-muted-foreground mt-1">
            Temporários, contratos administrativos com prazo determinado.
          </p>
        </li>
        <li className="rounded-md border p-3">
          <strong>Eletivos</strong>
          <p className="text-xs text-muted-foreground mt-1">
            Prefeito, Vice-Prefeito e Vereadores — exercem mandato.
          </p>
        </li>
      </ul>

      <h3 className="text-base font-semibold mt-4">Por área (secretaria)</h3>
      <p>
        Cada lotação tem uma natureza macro. Quando o sistema importa do
        Fiorilli, classifica automaticamente baseado em padrões no nome
        ("Escola" → Educação, "UBS/PSF" → Saúde, "CRAS" → Assistência, etc.).
        O admin do município pode reclassificar manualmente o que ficou em
        "Outros" pela tela de Lotações.
      </p>
      <ul className="grid grid-cols-1 sm:grid-cols-2 gap-2 pl-0 list-none">
        <li className="rounded-md border p-3">
          <strong>Administração</strong>
          <p className="text-xs text-muted-foreground mt-1">
            Gabinete, Finanças, Procuradoria, Recursos Humanos, Controladoria,
            Câmara.
          </p>
        </li>
        <li className="rounded-md border p-3">
          <strong>Saúde</strong>
          <p className="text-xs text-muted-foreground mt-1">
            SEMSA, UBS, Hospital, PSF/ESF, ACS, SAMU, Vigilância Sanitária.
          </p>
        </li>
        <li className="rounded-md border p-3">
          <strong>Educação</strong>
          <p className="text-xs text-muted-foreground mt-1">
            SEMED, escolas, creches, EMEF/EMEI, biblioteca.
          </p>
        </li>
        <li className="rounded-md border p-3">
          <strong>Assistência social</strong>
          <p className="text-xs text-muted-foreground mt-1">
            CRAS, CREAS, Conselho Tutelar, Bolsa Família, SCFV, Criança Feliz.
          </p>
        </li>
      </ul>
      <Callout variant="info">
        Lotações fora das 4 áreas macro (Cultura, Esporte, Obras, Meio
        Ambiente, Agricultura, Juventude, etc.) ficam classificadas como{" "}
        <strong>"Outros"</strong> e aparecem em uma seção própria no
        dashboard.
      </Callout>

      <h3 className="text-base font-semibold mt-4">Unidade orçamentária (origem do empenho)</h3>
      <p>
        Além da lotação física (onde o servidor trabalha) e do vínculo (tipo
        de contrato), o sistema também guarda a <strong>unidade
        orçamentária</strong> — de qual orçamento sai o empenho do salário.
        É essa a fonte de verdade da divisão por secretaria quando o
        Fiorilli SIP do município preenche o dado de despesa.
      </p>
      <p>
        Importamos 65 unidades orçamentárias do município-piloto, cada uma
        já classificada por área (saúde/educação/administração/assistência).
        No detalhe do servidor, cada vínculo mostra a unidade associada
        quando existe. Filtro por unidade está disponível no backend
        (<code className="text-xs bg-muted px-1 rounded">?natureza_unidade=saude</code>)
        e é a forma definitiva de responder "quem é da Saúde de verdade".
      </p>

      <h3 className="text-base font-semibold mt-4">No dia a dia</h3>
      <ul className="list-disc pl-5 space-y-1">
        <li>
          O <Link to="/" className="underline">Dashboard</Link> exibe contagens
          por vínculo e por área, cada card clicável navega para a lista
          filtrada.
        </li>
        <li>
          Em <Link to="/servidores" className="underline">Servidores</Link>,
          os filtros de vínculo e área se combinam — você consegue, por
          exemplo, "Efetivos da Saúde" em 2 cliques.
        </li>
        <li>
          A URL reflete os filtros, então o link
          <code className="text-xs bg-muted px-1 rounded mx-1">
            /servidores?regime=eletivo
          </code>
          pode ser compartilhado direto.
        </li>
      </ul>
    </Section>
  );
}

function SectionCadastros() {
  return (
    <Section id="cadastros" icon={Briefcase} title="Cadastros centrais">
      <p>
        Antes de admitir um servidor, você precisa ter as estruturas de apoio cadastradas:
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <FeatureCard
          icon={Briefcase}
          title="Cargos"
          to="/cargos"
          status="ok"
          desc="Cargos públicos (Professor, Auxiliar, etc.) com CBO, escolaridade exigida, vagas e atribuições. Cargos extintos podem ser desativados sem perder histórico."
        />
        <FeatureCard
          icon={Library}
          title="Lotações"
          to="/lotacoes"
          status="ok"
          desc="Secretarias, escolas, departamentos. Suporta hierarquia (lotação pai-filho) para refletir o organograma da prefeitura."
        />
        <FeatureCard
          icon={Tag}
          title="Rubricas"
          to="/rubricas"
          status="ok"
          desc="Proventos, descontos e rubricas informativas. A fórmula DSL é validada na criação e usada pelo motor de cálculo (Onda 2.1+). Veja a seção 'Folha de pagamento' para exemplos de fórmula e funções disponíveis."
        />
      </div>
      <p>Em todas essas telas você tem:</p>
      <ul className="list-disc pl-5 space-y-1">
        <li>Busca por código, nome ou outros campos relevantes.</li>
        <li>Filtros por status (ativo/inativo) e por tipo, quando aplicável.</li>
        <li>Ordenação clicável nas colunas.</li>
        <li>Criar / editar (slide-from-right) / ativar-desativar / excluir.</li>
      </ul>
    </Section>
  );
}

function SectionServidores() {
  return (
    <Section id="servidores" icon={Users} title="Servidores">
      <p>
        A tela de <Link to="/servidores" className="underline">Servidores</Link> é o
        coração da operação. Cada servidor tem dados pessoais, vínculos funcionais (com
        cargo, lotação, regime, salário-base e carga horária), dependentes e histórico
        funcional.
      </p>

      <h3 className="text-base font-semibold mt-4">Fluxos disponíveis</h3>
      <ul className="space-y-3">
        <FlowItem
          status="ok"
          title="Admitir servidor"
          desc="Botão na lista. Abre formulário com dados pessoais + dados do vínculo inicial. Cria Servidor + Vínculo em transação atômica — ou tudo dá certo, ou nada é salvo."
        />
        <FlowItem
          status="ok"
          title="Editar dados pessoais"
          desc="Botão 'Editar dados' no detalhe do servidor. Atualiza identificação, contato e endereço. Alterações ficam no histórico."
        />
        <FlowItem
          status="ok"
          title="Desligar servidor"
          desc="Botão 'Desligar' no detalhe (só aparece se ativo). Pede data e motivo opcional, encerra TODOS os vínculos ativos e marca o servidor como inativo. Atômico."
        />
        <FlowItem
          status="ok"
          title="Transferir vínculo"
          desc="Aba 'Vínculos' → menu de cada vínculo ativo → 'Transferir lotação'. Encerra o vínculo atual e cria um novo na nova lotação (mesmo cargo, regime e salário). Atômico."
        />
        <FlowItem
          status="ok"
          title="Cadastrar dependentes"
          desc="Aba 'Dependentes' → 'Novo dependente'. Marque as flags de IR e salário-família para que entrem no cálculo (Bloco 2)."
        />
        <FlowItem
          status="ok"
          title="Consultar histórico"
          desc="Aba 'Histórico'. Timeline com todas as mudanças do registro (criação, alterações, desligamento), com data, autor e snapshot dos campos."
        />
        <FlowItem
          status="ok"
          title="Ver unidade orçamentária do vínculo"
          desc="Cada vínculo no detalhe do servidor mostra a unidade orçamentária associada (de qual orçamento sai o empenho). É a fonte de verdade da divisão por secretaria — quando preenchida no SIP, o sistema importa e exibe automaticamente."
        />
        <FlowItem
          status="ok"
          title="Documentos digitalizados"
          desc="Aba 'Documentos' no detalhe do servidor. Upload (PDF/JPG/PNG até 10 MB) com tipo (RG, CPF, certificado, etc.) e descrição. Lista, download e exclusão."
        />
        <FlowItem
          status="ok"
          title="Filtrar cadastros incompletos para o eSocial"
          desc="Na lista de servidores, o filtro 'Cadastro: incompletos' mostra apenas quem ainda tem campos pré-eSocial em branco (tipo de logradouro, raça, nome da mãe, PIS, órgão emissor do vínculo, etc.). Use junto com a busca para fechar pendências por área."
        />
        <FlowItem
          status="ok"
          title="Editar em lote"
          desc="Selecione vários servidores com os checkboxes da lista (ou 'selecionar todos da página') e clique em 'Editar em lote'. Aplica os mesmos valores em todos de uma vez — útil quando uma secretaria inteira passa a usar o mesmo CEP/sindicato/órgão emissor. Campos deixados em branco não são alterados."
        />
        <FlowItem
          status="ok"
          title="Painel de qualidade cadastral"
          desc="A tela /qualidade-cadastral mostra o health score do município (0-100), quantos servidores estão prontos pra S-2200 e qual campo está em branco em mais cadastros. Clique nos cards para filtrar a lista pelo que falta."
        />
        <FlowItem
          status="ok"
          title="Importar planilha de enriquecimento"
          desc="Em /importar, anexe um CSV ou XLSX com matrícula/CPF + colunas de endereço, raça, nome da mãe, instrução, PIS etc. Pré-visualize (dry-run), confira o diff antes/depois e só então aplique. Colunas não reconhecidas são ignoradas sem erro."
        />
      </ul>

      <Callout variant="warning">
        <strong>Salário-base = R$ 0</strong> nos vínculos importados via SIP — isso é
        intencional. O Fiorilli guarda o salário em outras tabelas (eventos fixos +
        movimento histórico) que dependem do engine de cálculo. Por enquanto, edite
        cada vínculo e preencha o salário manualmente para testar o{" "}
        <a href="#folha" className="underline">cálculo da folha</a> (Onda 2.2 ✓).
      </Callout>
    </Section>
  );
}

function SectionConfiguracoes() {
  return (
    <Section id="configuracoes" icon={SettingsIcon} title="Configurações">
      <p>
        Acesse via <Link to="/configuracoes" className="underline">Configurações</Link>{" "}
        no rodapé da sidebar. A página tem 3 abas:
      </p>
      <ul className="space-y-3">
        <FlowItem
          status="ok"
          title="Perfil"
          desc="Edite seu nome completo. O e-mail é imutável — para alterar, fale com o suporte."
        />
        <FlowItem
          status="ok"
          title="Segurança"
          desc="Troque sua senha (precisa da senha atual + nova com mínimo 8 caracteres)."
        />
        <FlowItem
          status="ok"
          title="Usuários do município (admin)"
          desc="Lista todos os usuários com acesso ao município ativo. Cria novos com papel + senha temporária. Troca o papel direto na linha. Remove o acesso (sem deletar o usuário, que pode ter papel em outros municípios)."
        />
      </ul>
      <Callout variant="info">
        Apenas <code className="text-xs bg-muted px-1 rounded">admin_municipio</code> e{" "}
        <code className="text-xs bg-muted px-1 rounded">staff_arminda</code> veem a aba
        Usuários. Outros papéis veem só Perfil e Segurança.
      </Callout>
    </Section>
  );
}

function SectionAtalhos() {
  return (
    <Section id="atalhos" icon={Keyboard} title="Pesquisa e atalhos">
      <p>
        A barra de pesquisa global está sempre visível no topo. Aperte{" "}
        <kbd className="font-mono text-[11px] px-1.5 py-0.5 bg-muted border rounded-sm">⌘K</kbd>{" "}
        (Mac) ou{" "}
        <kbd className="font-mono text-[11px] px-1.5 py-0.5 bg-muted border rounded-sm">
          Ctrl+K
        </kbd>{" "}
        (Windows/Linux) em qualquer tela autenticada para abrir.
      </p>
      <ul className="list-disc pl-5 space-y-1">
        <li>
          A pesquisa busca em paralelo por <strong>servidores</strong> (matrícula, nome,
          CPF), <strong>cargos</strong> (código, nome, CBO),{" "}
          <strong>lotações</strong> (código, nome, sigla) e{" "}
          <strong>rubricas</strong> (código, nome).
        </li>
        <li>
          Vazio ou com menos de 2 caracteres: o palette mostra <strong>atalhos</strong>{" "}
          para todas as áreas do sistema (Dashboard, Servidores, Configurações, etc.).
        </li>
        <li>
          Use ↑/↓ para navegar entre resultados; Enter abre a página relevante; Esc fecha.
        </li>
      </ul>
      <Callout variant="tip">
        A pesquisa só vê dados do município ativo. Para buscar em outro município,
        troque-o primeiro pelo card da sidebar.
      </Callout>
    </Section>
  );
}

function SectionFolha() {
  return (
    <Section id="folha" icon={Wallet} title="Folha de pagamento">
      <p>
        O <strong>cálculo da folha mensal</strong> está disponível desde a Onda 2.2
        e agora tem <strong>tela operacional completa</strong> (Onda 2.6 ✓ em
        mai/2026). Em <Link to="/folha" className="underline">/folha</Link> você
        lista, cria, calcula e inspeciona competências. Cada folha tem três
        cards de totais (proventos / descontos / líquido) e tabs com lançamentos
        e erros estruturados.
      </p>

      <h3 className="text-base font-semibold mt-4">Como o cálculo funciona</h3>
      <ol className="list-decimal pl-5 space-y-2">
        <li>
          <strong>Cadastre as rubricas</strong> em{" "}
          <Link to="/rubricas" className="underline">/rubricas</Link> — código, nome,
          tipo (provento / desconto / informativa) e fórmula DSL.
        </li>
        <li>
          <strong>Defina a fórmula</strong> usando a DSL do Arminda. Exemplos:
          <pre className="mt-1 text-[11px] bg-muted px-2 py-1.5 rounded leading-relaxed overflow-x-auto">
{`SALARIO_BASE                          # salário base do vínculo
RUBRICA('SAL_BASE') * 0.11            # INSS 11% sobre rubrica
SE(DEPENDENTES > 0, 189.59 * DEPENDENTES, 0)
MAX(SALARIO_BASE, SALARIO_MINIMO)     # piso salarial
ARRED(SALARIO_BASE * 0.10, 2)         # arredondar p/ 2 casas`}
          </pre>
        </li>
        <li>
          <strong>Crie uma folha</strong> da competência desejada (POST{" "}
          <code className="text-xs bg-muted px-1 rounded">/api/payroll/folhas/</code>{" "}
          com <code className="text-xs bg-muted px-1 rounded">{`{ "competencia": "2026-05-01", "tipo": "mensal" }`}</code>).
        </li>
        <li>
          <strong>Dispare o cálculo</strong>: POST{" "}
          <code className="text-xs bg-muted px-1 rounded">
            /api/payroll/folhas/{`{id}`}/calcular/
          </code>
          . O sistema percorre todos os vínculos ativos × rubricas ativas em ordem
          topológica e produz um lançamento por par.
        </li>
        <li>
          <strong>Confira o relatório</strong>: a resposta traz contadores (vínculos
          processados, lançamentos criados/atualizados/removidos), a ordem em que as
          rubricas foram calculadas e a lista de erros por (vínculo, rubrica) — se
          uma fórmula falhou, o batch continua e reporta no fim.
        </li>
      </ol>

      <h3 className="text-base font-semibold mt-4">Variáveis disponíveis nas fórmulas</h3>
      <ul className="list-disc pl-5 space-y-1 text-xs">
        <li>
          <code className="bg-muted px-1 rounded">SALARIO_BASE</code> — salário do
          vínculo
        </li>
        <li>
          <code className="bg-muted px-1 rounded">CARGA_HORARIA</code>,{" "}
          <code className="bg-muted px-1 rounded">HORAS_PADRAO</code>,{" "}
          <code className="bg-muted px-1 rounded">HORAS_TRABALHADAS</code>
        </li>
        <li>
          <code className="bg-muted px-1 rounded">DIAS_TRABALHADOS</code>,{" "}
          <code className="bg-muted px-1 rounded">FALTAS</code>
        </li>
        <li>
          <code className="bg-muted px-1 rounded">IDADE</code>,{" "}
          <code className="bg-muted px-1 rounded">DEPENDENTES</code>,{" "}
          <code className="bg-muted px-1 rounded">DEPENDENTES_SALFAM</code>
        </li>
        <li>
          <code className="bg-muted px-1 rounded">TEMPO_SERVICO_ANOS</code>,{" "}
          <code className="bg-muted px-1 rounded">SALARIO_MINIMO</code>
        </li>
        <li>
          <code className="bg-muted px-1 rounded">COMPETENCIA_ANO</code>,{" "}
          <code className="bg-muted px-1 rounded">COMPETENCIA_MES</code>
        </li>
        <li>
          <strong>Incidências (Onda 2.4):</strong>{" "}
          <code className="bg-muted px-1 rounded">BASE_INSS</code>,{" "}
          <code className="bg-muted px-1 rounded">BASE_IRRF</code>,{" "}
          <code className="bg-muted px-1 rounded">BASE_FGTS</code>,{" "}
          <code className="bg-muted px-1 rounded">BASE_RPPS</code> (somas automáticas
          dos proventos marcados),{" "}
          <code className="bg-muted px-1 rounded">EH_RGPS</code>,{" "}
          <code className="bg-muted px-1 rounded">EH_RPPS</code>,{" "}
          <code className="bg-muted px-1 rounded">EH_FGTS</code> (1/0 por regime),{" "}
          <code className="bg-muted px-1 rounded">ALIQ_RPPS_PATRONAL</code>,{" "}
          <code className="bg-muted px-1 rounded">ALIQ_FGTS</code>
        </li>
      </ul>

      <h3 className="text-base font-semibold mt-4">Funções builtin</h3>
      <ul className="list-disc pl-5 space-y-1 text-xs">
        <li>
          <code className="bg-muted px-1 rounded">SE(condição, sim, não)</code>
        </li>
        <li>
          <code className="bg-muted px-1 rounded">MAX(a, b, …)</code>,{" "}
          <code className="bg-muted px-1 rounded">MIN(a, b, …)</code>,{" "}
          <code className="bg-muted px-1 rounded">ABS(x)</code>
        </li>
        <li>
          <code className="bg-muted px-1 rounded">ARRED(valor, casas)</code> —
          arredondamento bancário (half-even)
        </li>
        <li>
          <code className="bg-muted px-1 rounded">RUBRICA('CODIGO')</code> — valor de
          outra rubrica já calculada neste mesmo vínculo
        </li>
        <li>
          <code className="bg-muted px-1 rounded">FAIXA_IRRF(base, deps)</code> —
          IRRF progressivo conforme tabela legal vigente na competência (Onda 2.3 ✓)
        </li>
        <li>
          <code className="bg-muted px-1 rounded">FAIXA_INSS(base)</code> —
          INSS progressivo (faixas + teto) conforme tabela legal vigente (Onda 2.3 ✓)
        </li>
        <li>
          <code className="bg-muted px-1 rounded">FAIXA_RPPS(base)</code> —
          contribuição ao regime próprio (RPPS) conforme a config do município —
          alíquota única ou progressiva (Onda 2.4 ✓)
        </li>
      </ul>

      <h3 className="text-base font-semibold mt-4">Incidências e previdência (Onda 2.4)</h3>
      <p>
        As <strong>bases de incidência</strong> são calculadas automaticamente: marque
        em cada rubrica os encargos sobre os quais ela incide (INSS, IRRF, FGTS, RPPS)
        e o sistema soma os proventos para formar{" "}
        <code className="bg-muted px-1 rounded">BASE_INSS</code> etc. — não é mais
        preciso remontar a base na fórmula. O <strong>FGTS</strong> (8% patronal) entra
        como rubrica informativa para celetistas. A{" "}
        <strong>previdência própria (RPPS)</strong> é configurada em{" "}
        <Link to="/configuracoes" className="underline">Configurações → Previdência</Link>{" "}
        (alíquotas do servidor e patronal, modo único ou progressivo, regimes cobertos).
        Estatutários cobertos contribuem ao RPPS; os demais, ao INSS.
      </p>

      <h3 className="text-base font-semibold mt-4">Servidores, totais por área e holerite</h3>
      <p>
        Na folha, a aba <strong>Servidores</strong> mostra cada servidor uma vez com
        proventos, descontos e líquido, e um botão <strong>PDF</strong> que gera o{" "}
        <strong>holerite</strong> (cabeçalho do município, dados do servidor e do
        vínculo, proventos, descontos, totais, líquido e informativas como FGTS e RPPS
        patronal). A aba <strong>Por área</strong> traz os totais agrupados por lotação
        e por órgão emissor, mais o total geral. A aba <strong>Lançamentos</strong>{" "}
        continua disponível para a conferência detalhada (uma linha por rubrica). O
        holerite também sai em JSON para integrações.
      </p>

      <h3 className="text-base font-semibold mt-4">13º salário (Onda 3.1)</h3>
      <p>
        O 13º já pode ser calculado. Crie uma folha do tipo{" "}
        <strong>13º — 1ª parcela</strong> (adiantamento de 50%, sem descontos) ou{" "}
        <strong>13º — 2ª parcela</strong> (13º integral, com INSS/IRRF/RPPS sobre o
        13º calculados em separado e abatimento do adiantamento). O sistema calcula
        os <strong>avos</strong> automaticamente (meses trabalhados no ano, contando o
        mês com 15 dias ou mais), conforme a data de admissão de cada servidor. As
        rubricas de 13º vêm prontas pelo comando de seed; cada rubrica agora declara
        em quais tipos de folha ela entra, então a folha mensal e a de 13º não se
        misturam.
      </p>

      <h3 className="text-base font-semibold mt-4">Rescisão (Onda 3.2)</h3>
      <p>
        Ao <strong>desligar</strong> um servidor (em{" "}
        <Link to="/servidores" className="underline">/servidores</Link> → detalhe →
        Desligar), informe o <strong>motivo</strong> (pedido, dispensa sem/com justa
        causa, término, aposentadoria, etc.), se há <strong>aviso prévio indenizado</strong>,{" "}
        <strong>férias vencidas</strong> e o <strong>saldo do FGTS</strong>. Depois crie
        uma folha do tipo <strong>Rescisão</strong> na competência do desligamento e
        calcule: o sistema gera as verbas conforme o motivo — saldo de salário, 13º
        proporcional, férias proporcionais e vencidas + 1/3, aviso indenizado — com
        INSS/IRRF sobre as parcelas tributáveis (férias e aviso indenizados não tributam)
        e o FGTS + multa de 40% para celetistas sem justa causa.
      </p>

      <h3 className="text-base font-semibold mt-4">Férias (Onda 3.3)</h3>
      <p>
        Crie uma folha do tipo <strong>Férias</strong> e use a aba{" "}
        <strong>Programação</strong> para adicionar os servidores que sairão de
        férias, com os <strong>dias de gozo</strong> e os <strong>dias vendidos</strong>{" "}
        (abono pecuniário, até 10). Ao calcular, o sistema gera o salário de férias +
        1/3 constitucional (com INSS/IRRF) e o abono pecuniário + 1/3 (indenizado, sem
        desconto). O holerite e os resumos saem como em qualquer folha.
      </p>

      <h3 className="text-base font-semibold mt-4">Licença-prêmio (Onda 3.4)</h3>
      <p>
        Para pagar a <strong>indenização</strong> de licença-prêmio não gozada, crie
        uma folha do tipo <strong>Licença-prêmio</strong> e, na aba{" "}
        <strong>Programação</strong>, adicione os servidores com os meses (e dias) a
        indenizar. O valor é <code>salário × meses (+ salário/30 × dias)</code>, verba
        indenizatória — sem INSS nem IRRF. (Licença-prêmio gozada é a folha mensal
        normal.)
      </p>

      <h3 className="text-base font-semibold mt-4">Folha complementar (Onda 3.5)</h3>
      <p>
        Para pagar <strong>diferenças</strong> de uma competência que já foi fechada
        (reajuste retroativo, rubrica esquecida, correção), crie uma folha do tipo{" "}
        <strong>Complementar</strong> e, na aba <strong>Programação</strong>, lance
        para cada servidor a rubrica e o <strong>valor</strong> à mão. Os valores são
        explícitos — <strong>não há incidência automática</strong>: se houver INSS/IRRF
        complementar devido, lance-o também como desconto. (O cálculo automático da
        diferença e das incidências sobre a base do mês fica para uma evolução futura.)
      </p>

      <h3 className="text-base font-semibold mt-4">eSocial — primeiros eventos (Onda 4.1)</h3>
      <p>
        Começou o <strong>eSocial</strong>. No menu <strong>eSocial</strong>, escolha um{" "}
        <strong>órgão emissor</strong> (cada CNPJ tem o seu) e gere os eventos de
        tabela <strong>S-1000</strong> (informações do empregador) e{" "}
        <strong>S-1005</strong> (estabelecimentos). Cada evento gerado é{" "}
        <strong>validado contra o XSD oficial</strong> (layout S-1.3) e pode ser
        baixado em XML. Nesta etapa o sistema <strong>gera e valida</strong> o XML;
        a <strong>assinatura digital</strong> e o <strong>envio</strong> ao governo
        entram nas próximas ondas (dependem de certificado e acesso ao ambiente do
        eSocial).
      </p>
      <p>
        <strong>Tabela de rubricas (S-1010, Onda 4.3):</strong> cada rubrica agora
        pode receber a <strong>natureza eSocial (Tabela 3)</strong> e os códigos de
        incidência (previdência/IRRF/FGTS/RPPS) na tela de <strong>Rubricas</strong>.
        Com a natureza preenchida, gere o evento <strong>S-1010</strong> da rubrica no
        menu eSocial — também validado contra o XSD. Isso é o pré-requisito dos
        eventos de remuneração (S-1200/S-1202) que virão.
      </p>
      <p>
        <strong>Certificado digital e assinatura (Onda 4.2):</strong> no menu eSocial,
        ao escolher um órgão, você pode <strong>guardar o certificado digital (.pfx)</strong>{" "}
        daquele CNPJ no cofre — ele fica <strong>cifrado</strong>, e a senha nunca é
        exibida. Com o certificado guardado, o botão <strong>Assinar</strong> aplica a{" "}
        <strong>assinatura digital (ICP-Brasil)</strong> ao evento, que passa a valer
        perante o governo. Falta só a <strong>transmissão</strong> ao eSocial, na próxima
        onda.
      </p>

      <h3 className="text-base font-semibold mt-4">Retrato fiscal da folha (Onda 4.4)</h3>
      <p>
        Cada lançamento calculado agora guarda um <strong>retrato fiscal congelado</strong>{" "}
        (as incidências e a natureza eSocial da rubrica naquele momento) — editar uma
        rubrica depois <strong>não altera folhas já calculadas</strong>, e folha{" "}
        <strong>fechada não pode ser recalculada</strong> (exigência de auditoria). O
        sistema também passa a guardar o <strong>resumo consolidado por servidor</strong>{" "}
        em cada folha (totais + bases de INSS/IRRF/FGTS/RPPS) — é o insumo direto dos
        eventos de remuneração do eSocial que vêm a seguir.
      </p>
      <p>
        <strong>Exportar a folha em PDF:</strong> na tela da folha, o botão{" "}
        <strong>Exportar PDF</strong> gera o relatório analítico completo — quadro
        geral, uma linha por servidor (proventos/descontos/líquido) e totais por
        lotação e por órgão emissor. Pronto para imprimir, anexar a processo ou
        enviar ao controle interno.
      </p>

      <h3 className="text-base font-semibold mt-4">O que está pronto e o que vem</h3>
      <ul className="space-y-3">
        <FlowItem
          status="ok"
          title="Calculadora de fórmulas"
          desc="POST /api/payroll/rubricas/{id}/avaliar/ — testa uma fórmula com um contexto manual. Útil para depurar antes de fechar a competência."
        />
        <FlowItem
          status="ok"
          title="Cálculo mensal ordinário"
          desc="POST /api/payroll/folhas/{id}/calcular/ — produz lançamentos para todos os vínculos ativos da competência. Idempotente (recalcular não duplica). Coleta erros por par sem parar o batch."
        />
        <FlowItem
          status="ok"
          title="Consulta de lançamentos"
          desc="GET /api/payroll/lancamentos/?folha={id} — paginado, com filtros por servidor, rubrica, tipo e valor."
        />
        <FlowItem
          status="ok"
          title="Tabelas legais 2024/2025/2026 (INSS, IRRF, salário mínimo)"
          desc="Onda 2.3 ✓ — FAIXA_INSS e FAIXA_IRRF reais (faixas progressivas conferidas contra calculadora oficial da Receita); SALARIO_MINIMO dinâmico por competência; admin Django para atualizar a cada virada de exercício, sem deploy."
        />
        <FlowItem
          status="em-construcao"
          title="Holerite (PDF)"
          desc="Onda 2.5 — gera contracheque a partir dos lançamentos da folha calculada."
        />
        <FlowItem
          status="ok"
          title="Tela operacional de Folha"
          desc="Onda 2.6 ✓ — /folha lista as competências; cada uma tem detalhe com botão Calcular/Recalcular (idempotente), relatório do último cálculo, lançamentos paginados com filtro por servidor e rubrica, aba de erros estruturados."
        />
      </ul>

      <Callout variant="warning">
        Hoje os salários dos vínculos importados via SIP vêm zerados (intencional,
        ver bloco Servidores). Para testar o cálculo, preencha{" "}
        <strong>salario_base</strong> manualmente nos vínculos antes de disparar.
      </Callout>

      <Callout variant="info">
        Erros de fórmula têm <strong>código estável</strong> que vai aparecer na UI
        da Onda 2.6 com mensagem amigável:{" "}
        <code className="text-xs bg-muted px-1 rounded">FORMULA_SINTAXE</code>,{" "}
        <code className="text-xs bg-muted px-1 rounded">FORMULA_VARIAVEL_AUSENTE</code>,{" "}
        <code className="text-xs bg-muted px-1 rounded">FORMULA_FUNCAO_DESCONHECIDA</code>,{" "}
        <code className="text-xs bg-muted px-1 rounded">FORMULA_DIVISAO_POR_ZERO</code>,{" "}
        <code className="text-xs bg-muted px-1 rounded">DEPENDENCIA_CICLICA</code> etc.
      </Callout>
    </Section>
  );
}

function SectionImportador() {
  return (
    <Section id="importador" icon={Upload} title="Importador Fiorilli SIP">
      <p>
        Pipeline ETL unidirecional do banco legado SIP (Firebird 2.5) para o schema do
        município no Postgres. <Status status="ok" inline />
      </p>
      <h3 className="text-base font-semibold mt-4">O que importa</h3>
      <ul className="list-disc pl-5 space-y-1">
        <li>
          <strong>Cadastros</strong> (entrega atual): cargos, lotações (a partir de
          LOCAL_TRABALHO), servidores (a partir de PESSOA), vínculos funcionais
          (TRABALHADOR), dependentes.
        </li>
        <li>
          <strong>Histórico financeiro</strong> (eventos fixos, movimento mensal): só
          depois do Bloco 2, quando houver engine de cálculo.
        </li>
      </ul>
      <h3 className="text-base font-semibold mt-4">Garantias</h3>
      <ul className="list-disc pl-5 space-y-1">
        <li>
          <strong>Idempotente</strong> — rodar várias vezes produz o mesmo resultado
          final. Use chave SIP estável (<code className="text-xs bg-muted px-1 rounded">EMPRESA-CODIGO</code>{" "}
          ou CPF).
        </li>
        <li>
          <strong>Linha com erro não para o batch</strong> — erros vão para o registro de
          auditoria <code className="text-xs bg-muted px-1 rounded">SipImportRecord</code>;
          o resto continua.
        </li>
        <li>
          <strong>Modo dry-run</strong> faz rollback no fim — útil para validar antes de
          commitar.
        </li>
      </ul>
      <Callout variant="info">
        O importador é executado por linha de comando pelo administrador técnico, não pela
        UI. Veja{" "}
        <code className="text-xs bg-muted px-1 rounded">
          docs/adr/0009-importador-fiorilli-sip.md
        </code>{" "}
        para o procedimento completo.
      </Callout>
    </Section>
  );
}

function SectionEmConstrucao() {
  return (
    <Section id="em-construcao" icon={Construction} title="Em construção (próximos blocos)">
      <p>
        O Arminda é entregue por blocos sequenciais. Abaixo, o que ainda virá e quando.
        Datas-alvo são do roadmap atual e podem ser ajustadas.
      </p>
      <ul className="space-y-3">
        <RoadmapItem
          icon={Wallet}
          title="Bloco 2 — Engine de cálculo de folha"
          period="Maio – Agosto/2026 (em andamento)"
          desc="DSL de fórmulas (2.1 ✓), cálculo mensal (2.2 ✓), tabelas legais 2024–2026 reais (2.3 ✓), tela operacional de Folha com lista, detalhe, calcular e tabs de lançamentos (2.6 ✓). Próximas: incidências FGTS e previdência municipal (2.4), holerite em PDF (2.5), paridade contra Fiorilli (2.7)."
        />
        <RoadmapItem
          icon={Wallet}
          title="Bloco 3 — Folhas especiais"
          period="Setembro/2026"
          desc="13º (1ª e 2ª parcelas), férias com abono e adiantamento, rescisões, licença-prêmio, folha complementar."
        />
        <RoadmapItem
          icon={FileText}
          title="Bloco 4 — Obrigações federais"
          period="Outubro – Novembro/2026"
          desc="eSocial (S-1000…S-2400), SEFIP, CAGED, RAIS, DIRF, DCTFWeb, MANAD (auditoria Receita/INSS) e informe de rendimentos. Tudo gerado por CNPJ do órgão emissor (Prefeitura, Fundo de Saúde, Fundo de Assistência, Câmara) — não pelo município como um todo."
        />
        <RoadmapItem
          icon={FileText}
          title="Bloco 5 — Tribunal de Contas"
          period="Dezembro/2026"
          desc="Adaptadores TCE-MA (SACOP/SIGFIS) e TCE-PB (Sagres Folha), framework extensível para outros estados, geração e validação de remessas, histórico de envios. Cada município ativa só as integrações que precisa pelo admin (ADR-0011) — o menu do frontend monta-se dinamicamente."
        />
        <RoadmapItem
          icon={Users}
          title="Bloco 6 — Operação piloto"
          period="Janeiro/2027"
          desc="Operação paralela em município real por 3 competências, validação cruzada, treinamento da equipe da prefeitura."
        />
        <RoadmapItem
          icon={SettingsIcon}
          title="Bloco 7 — Diferenciação"
          period="Fevereiro – Abril/2027"
          desc="Portal do servidor (web + mobile), bot WhatsApp, painéis em tempo real, alertas inteligentes, importador universal, API pública."
        />
      </ul>
      <p className="text-sm text-muted-foreground">
        Roadmap completo no{" "}
        <a
          href="/status-page/"
          className="underline inline-flex items-center gap-1"
          target="_blank"
          rel="noreferrer"
        >
          painel de status <ExternalLink className="h-3 w-3" />
        </a>
        .
      </p>
    </Section>
  );
}

function SectionSuporte() {
  return (
    <Section id="suporte" icon={Lightbulb} title="Suporte">
      <p>
        Para dúvidas operacionais e problemas técnicos, fale com{" "}
        <a href="mailto:suporte@arminda.app" className="underline">
          suporte@arminda.app
        </a>
        .
      </p>
      <p>
        Para reportar bugs ou sugerir melhorias, registre um chamado com:
      </p>
      <ul className="list-disc pl-5 space-y-1">
        <li>O que você esperava que acontecesse</li>
        <li>O que aconteceu</li>
        <li>Município ativo + papel do usuário</li>
        <li>Hora aproximada do incidente</li>
      </ul>
    </Section>
  );
}

// ============================================================
// Componentes auxiliares (locais para manter o arquivo autônomo)
// ============================================================

function Section({
  id,
  icon: Icon,
  title,
  children,
}: {
  id: string;
  icon: typeof Info;
  title: string;
  children: ReactNode;
}) {
  return (
    <section id={id} className="space-y-3 scroll-mt-20">
      <h2 className="font-semibold inline-flex items-center gap-2" style={{ fontSize: 18 }}>
        <Icon className="h-4.5 w-4.5 text-primary" />
        {title}
      </h2>
      <div className="space-y-3 text-sm leading-relaxed">{children}</div>
    </section>
  );
}

type StatusKind = "ok" | "parcial" | "em-construcao" | "futuro";

function Status({ status, inline }: { status: StatusKind; inline?: boolean }) {
  const variant = (
    {
      ok: "success",
      parcial: "warning",
      "em-construcao": "info",
      futuro: "muted",
    } as const
  )[status];
  const label = (
    {
      ok: "Disponível",
      parcial: "Parcial",
      "em-construcao": "Em construção",
      futuro: "No roadmap",
    } as const
  )[status];
  const Icon = (
    {
      ok: CheckCircle2,
      parcial: AlertCircle,
      "em-construcao": Construction,
      futuro: Lock,
    } as const
  )[status];
  return (
    <span className={inline ? "inline" : "ml-2"}>
      <Badge variant={variant} className="inline-flex items-center gap-1">
        <Icon className="h-3 w-3" />
        {label}
      </Badge>
    </span>
  );
}

function FeatureCard({
  icon: Icon,
  title,
  to,
  status,
  desc,
}: {
  icon: typeof Info;
  title: string;
  to: string;
  status: StatusKind;
  desc: string;
}) {
  return (
    <Card>
      <CardContent className="py-4 space-y-2">
        <div className="flex items-center justify-between gap-2">
          <Link
            to={to}
            className="inline-flex items-center gap-2 font-medium hover:underline"
          >
            <Icon className="h-4 w-4 text-muted-foreground" />
            {title}
          </Link>
          <Status status={status} inline />
        </div>
        <p className="text-xs text-muted-foreground">{desc}</p>
      </CardContent>
    </Card>
  );
}

function FlowItem({
  status,
  title,
  desc,
}: {
  status: StatusKind;
  title: string;
  desc: string;
}) {
  return (
    <li className="flex flex-col gap-1.5 rounded-md border p-3">
      <div className="flex items-center gap-2">
        <span className="font-medium text-sm">{title}</span>
        <Status status={status} inline />
      </div>
      <p className="text-xs text-muted-foreground">{desc}</p>
    </li>
  );
}

function RoadmapItem({
  icon: Icon,
  title,
  period,
  desc,
}: {
  icon: typeof Info;
  title: string;
  period: string;
  desc: string;
}) {
  return (
    <li className="flex gap-3 rounded-md border p-3">
      <span className="inline-flex h-8 w-8 items-center justify-center rounded-md bg-muted text-muted-foreground flex-shrink-0">
        <Icon className="h-4 w-4" />
      </span>
      <div className="flex-1 space-y-1">
        <div className="flex items-center justify-between gap-2 flex-wrap">
          <span className="font-medium text-sm">{title}</span>
          <span className="text-xs text-muted-foreground font-mono">{period}</span>
        </div>
        <p className="text-xs text-muted-foreground">{desc}</p>
      </div>
    </li>
  );
}

function Callout({
  variant,
  children,
}: {
  variant: "info" | "warning" | "tip";
  children: ReactNode;
}) {
  const styles = {
    info: "bg-info-soft text-info-soft-foreground border-info-soft",
    warning: "bg-warning-soft text-warning-soft-foreground border-warning-soft",
    tip: "bg-success-soft text-success-soft-foreground border-success-soft",
  }[variant];
  const Icon = { info: Info, warning: AlertCircle, tip: Lightbulb }[variant];
  return (
    <div className={`flex gap-2.5 rounded-md border p-3 text-xs ${styles}`}>
      <Icon className="h-4 w-4 shrink-0 mt-0.5" />
      <div className="leading-relaxed">{children}</div>
    </div>
  );
}

// ============================================================
// Helpers
// ============================================================

function formatDate(iso: string): string {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}
