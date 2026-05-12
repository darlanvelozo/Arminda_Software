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

const LAST_UPDATED = "2026-05-10";

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
          <span className="ml-1 inline-flex items-center gap-1">
            <Badge variant="success">Bloco 1 entregue</Badge>
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
          status="parcial"
          desc="Proventos, descontos e rubricas informativas. O cadastro funciona, mas a fórmula de cálculo (DSL) só será interpretada no Bloco 2 — engine de cálculo de folha."
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
      </ul>

      <Callout variant="warning">
        <strong>Salário-base = R$ 0</strong> nos vínculos importados via SIP — isso é
        intencional. O Fiorilli guarda o salário em outras tabelas (eventos fixos +
        movimento histórico) que dependem do engine de cálculo (Bloco 2). Por enquanto,
        edite cada vínculo e preencha manualmente se quiser testar fluxos.
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
          period="Julho – Agosto/2026"
          desc="DSL de fórmulas para rubricas, cálculo mensal ordinário, incidências (INSS, IRRF, FGTS, previdência), holerite. Habilita as áreas Folha e KPIs do Dashboard."
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
          desc="eSocial, SEFIP, CAGED, RAIS, DIRF, informe de rendimentos, DCTFWeb. Habilita a área de Relatórios."
        />
        <RoadmapItem
          icon={FileText}
          title="Bloco 5 — Tribunal de Contas"
          period="Dezembro/2026"
          desc="Adaptador para TCE-MA (primeiro), framework para outros TCEs, geração e validação de remessas, histórico de envios."
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
