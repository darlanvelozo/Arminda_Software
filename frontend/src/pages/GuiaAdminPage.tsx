/**
 * GuiaAdminPage — Guia do desenvolvedor do Arminda.
 *
 * Visão de quem desenvolve: arquitetura, como rodar local, onde fica cada
 * coisa, política de versionamento, rotina de validação integral, como
 * adicionar uma onda nova. Não é manual de uso operacional — para isso
 * existe /guia.
 *
 * Acesso: rota protegida, visível só para staff_arminda / admin_municipio
 * (a navegação no Topbar é condicional).
 *
 * Atualizar SEMPRE que:
 *  - Uma onda fechar.
 *  - Um ADR novo for criado.
 *  - A estrutura de pastas mudar.
 *  - A rotina de validação mudar.
 *  - Um novo serviço externo for integrado.
 */

import {
  Activity,
  Box,
  Code2,
  Database,
  FileCode,
  FileText,
  FolderTree,
  GitBranch,
  HardDrive,
  Info,
  Layers,
  Lightbulb,
  Map,
  Package,
  PlayCircle,
  Server,
  ShieldCheck,
  Tag,
  TerminalSquare,
  TestTube2,
  Workflow,
} from "lucide-react";
import type { ReactNode } from "react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

const LAST_UPDATED = "2026-05-15";

interface TocItem {
  id: string;
  label: string;
  icon: typeof Info;
}

const TOC: TocItem[] = [
  { id: "panorama", label: "Panorama", icon: Info },
  { id: "estrutura", label: "Estrutura de pastas", icon: FolderTree },
  { id: "stack", label: "Stack técnico", icon: Layers },
  { id: "rodar-local", label: "Rodar localmente", icon: PlayCircle },
  { id: "modelo-dados", label: "Modelo de dados", icon: Database },
  { id: "tenants", label: "Multi-tenant (django-tenants)", icon: Box },
  { id: "auth-rbac", label: "Auth + RBAC", icon: ShieldCheck },
  { id: "dsl", label: "DSL de fórmulas (Bloco 2)", icon: FileCode },
  { id: "calculo", label: "Cálculo de folha (Onda 2.2)", icon: Workflow },
  { id: "testes", label: "Testes (back + front)", icon: TestTube2 },
  { id: "versionamento", label: "Versionamento (ADR-0010)", icon: Tag },
  { id: "validacao", label: "Rotina de validação integral", icon: Activity },
  { id: "nova-onda", label: "Como entregar uma onda", icon: GitBranch },
  { id: "manter-guias", label: "Manter os guias atualizados", icon: Map },
  { id: "docs", label: "Mapa de documentos", icon: FileText },
  { id: "ambientes", label: "Ambientes & deploy", icon: Server },
  { id: "memoria", label: "Memória do Claude", icon: HardDrive },
];

export default function GuiaAdminPage() {
  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <h1 className="font-semibold inline-flex items-center gap-2" style={{ fontSize: 22 }}>
          <TerminalSquare className="h-5 w-5 text-primary" />
          Guia do desenvolvedor
        </h1>
        <p className="text-sm text-muted-foreground">
          Visão de quem constrói o Arminda. Como rodar, onde fica cada coisa, como
          entregar uma onda nova. Diferente do{" "}
          <a href="/guia" className="underline">
            /guia
          </a>{" "}
          (manual operacional) — aqui é a referência técnica.
        </p>
        <p className="text-xs text-muted-foreground">
          Última atualização: <strong>{formatDate(LAST_UPDATED)}</strong>
          <span className="ml-1 inline-flex items-center gap-2">
            <Badge variant="info">Onda 2.2 + validação integral</Badge>
          </span>
        </p>
      </header>

      <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
        <aside className="hidden lg:block">
          <nav aria-label="Sumário" className="sticky top-4 space-y-1 text-sm">
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
          <SectionPanorama />
          <SectionEstrutura />
          <SectionStack />
          <SectionRodarLocal />
          <SectionModeloDados />
          <SectionTenants />
          <SectionAuthRBAC />
          <SectionDSL />
          <SectionCalculo />
          <SectionTestes />
          <SectionVersionamento />
          <SectionValidacao />
          <SectionNovaOnda />
          <SectionManterGuias />
          <SectionDocs />
          <SectionAmbientes />
          <SectionMemoria />
        </article>
      </div>
    </div>
  );
}

// ============================================================
// Seções
// ============================================================

function SectionPanorama() {
  return (
    <Section id="panorama" icon={Info} title="Panorama">
      <p>
        Arminda é um SaaS de folha de pagamento e gestão de pessoal para prefeituras
        brasileiras. <strong>Multi-tenant por schema</strong> (cada município isolado
        no PostgreSQL), <strong>Decimal puro</strong> (nada de float em dinheiro),{" "}
        <strong>idempotência</strong> em toda operação de batch, <strong>RBAC</strong>{" "}
        por papel × município, <strong>audit log</strong> via simple-history.
      </p>
      <p>
        Entrega por <strong>blocos</strong> (0–7) subdivididos em <strong>ondas</strong>{" "}
        (1.1, 1.2, … 2.1, 2.2). Cada onda fechada = 1 commit + 1 tag anotada
        (versionamento ADR-0010).
      </p>
      <p>
        Estado atual: Bloco 1 fechado, Bloco 2 em andamento — DSL (Onda 2.1) e
        cálculo mensal (Onda 2.2) já no ar, próximas ondas: tabelas legais,
        holerite, tela de folha.
      </p>
    </Section>
  );
}

function SectionEstrutura() {
  return (
    <Section id="estrutura" icon={FolderTree} title="Estrutura de pastas">
      <pre className="text-[11px] bg-muted px-3 py-2 rounded leading-relaxed overflow-x-auto">
{`Arminda_Software/
├── backend/                      Django 5.1 + DRF
│   ├── apps/
│   │   ├── core/                 SHARED: Municipio, Domain, Usuario, RBAC
│   │   ├── people/               TENANT: Servidor, Vinculo, Cargo, Lotacao
│   │   ├── payroll/              TENANT: Rubrica, Folha, Lancamento
│   │   ├── calculo/              TENANT: engine DSL + dependencias (toposort)
│   │   ├── imports/              SHARED: importador Fiorilli SIP
│   │   └── reports/              TENANT: relatórios (Bloco 2.5+)
│   ├── arminda/settings/         dev.py, test.py, prod.py
│   ├── conftest.py               fixtures globais de teste
│   └── pyproject.toml            ruff + pytest config
│
├── frontend/                     Vite + React + TS
│   ├── src/
│   │   ├── pages/                rotas top-level (lazy)
│   │   ├── components/           ui/, layout/, search/
│   │   ├── lib/                  api client, auth, query
│   │   └── types/api.ts          gerado de OpenAPI schema
│   └── package.json
│
├── docs/
│   ├── ROADMAP.md                Blocos 0–7, ondas, cronograma
│   ├── ARCHITECTURE.md           decisões macro
│   ├── adr/                      ADRs (decisões versionadas)
│   ├── leiautes/                 layouts externos (MANAD etc.)
│   └── relatorios/               relatórios quinzenais (HTML)
│
├── status-page/                  GitHub Pages — painel público
│   ├── index.html
│   ├── status.json               fonte da verdade (lido por JS)
│   └── assets/                   script.js, styles.css
│
├── CHANGELOG.md                  toda alteração relevante
└── .github/workflows/            backend-ci, frontend-ci, status-page`}
      </pre>
      <Callout variant="info">
        <strong>SHARED vs TENANT:</strong> apps em <code className="text-xs bg-muted px-1 rounded">SHARED_APPS</code>{" "}
        (core, imports) ficam no schema <code className="text-xs bg-muted px-1 rounded">public</code>;{" "}
        <code className="text-xs bg-muted px-1 rounded">TENANT_APPS</code> (people,
        payroll, calculo, reports) vivem em um schema por município (
        <code className="text-xs bg-muted px-1 rounded">Municipio.schema_name</code>).
      </Callout>
    </Section>
  );
}

function SectionStack() {
  return (
    <Section id="stack" icon={Layers} title="Stack técnico">
      <div className="grid gap-3 sm:grid-cols-2">
        <TechCard
          title="Backend"
          items={[
            "Python 3.12",
            "Django 5.1 + DRF",
            "PostgreSQL 16",
            "django-tenants (multi-schema)",
            "simple-history (audit)",
            "djangorestframework-simplejwt (auth)",
            "drf-spectacular (OpenAPI)",
            "ruff (lint/format)",
            "pytest + pytest-django + pytest-cov",
          ]}
        />
        <TechCard
          title="Frontend"
          items={[
            "Node 20+ / npm",
            "Vite 6 + React 19 + TypeScript",
            "Tailwind CSS + shadcn/ui",
            "TanStack Query (cache de API)",
            "react-hook-form + zod",
            "react-router-dom v6 (lazy routes)",
            "ESLint + Prettier",
            "Vitest + Testing Library",
          ]}
        />
      </div>
    </Section>
  );
}

function SectionRodarLocal() {
  return (
    <Section id="rodar-local" icon={PlayCircle} title="Rodar localmente">
      <h3 className="text-base font-semibold">Backend</h3>
      <pre className="text-[11px] bg-muted px-3 py-2 rounded leading-relaxed overflow-x-auto">
{`cd backend
source .venv/bin/activate           # ou python -m venv .venv && pip install -r requirements.txt
python manage.py migrate            # cria/atualiza schemas
python manage.py runserver 8000`}
      </pre>

      <h3 className="text-base font-semibold mt-4">Frontend</h3>
      <pre className="text-[11px] bg-muted px-3 py-2 rounded leading-relaxed overflow-x-auto">
{`cd frontend
npm install
npm run dev                         # http://localhost:5173`}
      </pre>

      <h3 className="text-base font-semibold mt-4">Variáveis de ambiente</h3>
      <ul className="list-disc pl-5 space-y-1 text-xs">
        <li>
          Backend: <code className="bg-muted px-1 rounded">DATABASE_URL</code>,{" "}
          <code className="bg-muted px-1 rounded">DJANGO_SECRET_KEY</code>,{" "}
          <code className="bg-muted px-1 rounded">DJANGO_DEBUG</code>,{" "}
          <code className="bg-muted px-1 rounded">SIP_PASSWORD</code> (importador).
        </li>
        <li>
          Frontend: <code className="bg-muted px-1 rounded">VITE_API_BASE_URL</code>{" "}
          (default <code className="bg-muted px-1 rounded">http://localhost:8000</code>).
        </li>
      </ul>

      <h3 className="text-base font-semibold mt-4">Header obrigatório nas chamadas tenant</h3>
      <p className="text-sm">
        Todo endpoint sob <code className="text-xs bg-muted px-1 rounded">/api/people/*</code>{" "}
        e <code className="text-xs bg-muted px-1 rounded">/api/payroll/*</code> exige{" "}
        <code className="text-xs bg-muted px-1 rounded">X-Tenant: &lt;schema_name&gt;</code>.
      </p>
    </Section>
  );
}

function SectionModeloDados() {
  return (
    <Section id="modelo-dados" icon={Database} title="Modelo de dados (resumo)">
      <h3 className="text-base font-semibold">SHARED (public)</h3>
      <ul className="list-disc pl-5 space-y-1 text-xs">
        <li>
          <code className="bg-muted px-1 rounded">Municipio</code>,{" "}
          <code className="bg-muted px-1 rounded">Domain</code> — tenant.
        </li>
        <li>
          <code className="bg-muted px-1 rounded">Usuario</code> (email é PK),{" "}
          <code className="bg-muted px-1 rounded">UsuarioMunicipioPapel</code> (RBAC
          M:N usuário × município × grupo).
        </li>
        <li>
          <code className="bg-muted px-1 rounded">SipImportRecord</code> — auditoria
          do importador (chave SIP → ID Arminda + hash do payload).
        </li>
      </ul>

      <h3 className="text-base font-semibold mt-4">TENANT (por schema)</h3>
      <ul className="list-disc pl-5 space-y-1 text-xs">
        <li>
          <strong>people:</strong> <code className="bg-muted px-1 rounded">Servidor</code>,{" "}
          <code className="bg-muted px-1 rounded">VinculoFuncional</code> (FK servidor
          + cargo + lotacao + unidade_orcamentaria + regime),{" "}
          <code className="bg-muted px-1 rounded">Cargo</code>,{" "}
          <code className="bg-muted px-1 rounded">Lotacao</code>,{" "}
          <code className="bg-muted px-1 rounded">UnidadeOrcamentaria</code>,{" "}
          <code className="bg-muted px-1 rounded">Dependente</code>,{" "}
          <code className="bg-muted px-1 rounded">Documento</code>.
        </li>
        <li>
          <strong>payroll:</strong>{" "}
          <code className="bg-muted px-1 rounded">Rubrica</code> (codigo, tipo,
          formula),{" "}
          <code className="bg-muted px-1 rounded">Folha</code> (competencia, tipo,
          status, totais),{" "}
          <code className="bg-muted px-1 rounded">Lancamento</code> (folha × vínculo
          × rubrica × valor).
        </li>
        <li>
          <strong>calculo:</strong> sem modelos — só código (DSL + toposort).
        </li>
      </ul>

      <Callout variant="info">
        Todos os Decimal usam <code className="text-xs bg-muted px-1 rounded">max_digits=12, decimal_places=2</code>{" "}
        para dinheiro e <code className="text-xs bg-muted px-1 rounded">decimal_places=4</code>{" "}
        para referência (quantidade, percentual, dias).
      </Callout>
    </Section>
  );
}

function SectionTenants() {
  return (
    <Section id="tenants" icon={Box} title="Multi-tenant (django-tenants)">
      <p>
        Cada município é um <strong>schema</strong> PostgreSQL. Roteamento por{" "}
        <strong>header HTTP</strong> (<code className="text-xs bg-muted px-1 rounded">X-Tenant</code>),
        não por domínio — escolhido por simplificar deploy num único domínio.
      </p>
      <ul className="list-disc pl-5 space-y-1 text-xs">
        <li>
          Middleware <code className="bg-muted px-1 rounded">XTenantMiddleware</code>{" "}
          (em <code className="bg-muted px-1 rounded">apps/core/middleware.py</code>)
          lê o header, valida que o usuário tem papel no município e troca o schema
          do connection.
        </li>
        <li>
          Em testes use o context manager{" "}
          <code className="bg-muted px-1 rounded">schema_context(tenant.schema_name)</code>{" "}
          do django-tenants. Há fixtures <code className="bg-muted px-1 rounded">tenant_a</code>,{" "}
          <code className="bg-muted px-1 rounded">tenant_b</code> em{" "}
          <code className="bg-muted px-1 rounded">backend/conftest.py</code>.
        </li>
        <li>
          O playbook completo está em{" "}
          <code className="bg-muted px-1 rounded">docs/MULTI_TENANT_PLAYBOOK.md</code>.
        </li>
      </ul>
    </Section>
  );
}

function SectionAuthRBAC() {
  return (
    <Section id="auth-rbac" icon={ShieldCheck} title="Auth + RBAC">
      <p>
        <strong>JWT</strong> via{" "}
        <code className="text-xs bg-muted px-1 rounded">djangorestframework-simplejwt</code>.
        Login devolve <code className="text-xs bg-muted px-1 rounded">access</code> +{" "}
        <code className="text-xs bg-muted px-1 rounded">refresh</code>. O frontend
        guarda em <code className="text-xs bg-muted px-1 rounded">localStorage</code>{" "}
        (auth-storage.ts).
      </p>
      <p>
        <strong>RBAC</strong>: 5 grupos seed (
        <code className="text-xs bg-muted px-1 rounded">staff_arminda</code>,{" "}
        <code className="text-xs bg-muted px-1 rounded">admin_municipio</code>,{" "}
        <code className="text-xs bg-muted px-1 rounded">rh_municipio</code>,{" "}
        <code className="text-xs bg-muted px-1 rounded">financeiro_municipio</code>,{" "}
        <code className="text-xs bg-muted px-1 rounded">leitura_municipio</code>),
        atribuídos via{" "}
        <code className="text-xs bg-muted px-1 rounded">UsuarioMunicipioPapel</code>{" "}
        (usuário × município × grupo). Permissões custom em{" "}
        <code className="text-xs bg-muted px-1 rounded">apps/core/permissions.py</code>.
      </p>
      <Callout variant="warning">
        <strong>Nunca use is_staff</strong> para gating de feature de município —
        is_staff é só para staff Arminda cross-tenant. Use{" "}
        <code className="text-xs bg-muted px-1 rounded">IsFinanceiroMunicipio</code>,{" "}
        <code className="text-xs bg-muted px-1 rounded">IsLeituraMunicipio</code>{" "}
        etc.
      </Callout>
    </Section>
  );
}

function SectionDSL() {
  return (
    <Section id="dsl" icon={FileCode} title="DSL de fórmulas (Bloco 2)">
      <p>
        Entregue na Onda 2.1 (ADR-0012). Subset seguro de Python validado por{" "}
        <strong>AST whitelist</strong>. Vive em{" "}
        <code className="text-xs bg-muted px-1 rounded">backend/apps/calculo/formula/</code>.
      </p>
      <h3 className="text-base font-semibold mt-4">Pipeline</h3>
      <ol className="list-decimal pl-5 space-y-1 text-xs">
        <li>
          <code className="bg-muted px-1 rounded">parser.py</code> — compila a
          fórmula em bytecode, valida AST (rejeita import, attribute, subscript,
          lambda, comprehension, pow, floor div, kwargs), substitui literais
          numéricos por <code className="bg-muted px-1 rounded">_D("0.10")</code>{" "}
          em runtime via <code className="bg-muted px-1 rounded">_NumericToDecimalTransformer</code>.
          Cacheado com <code className="bg-muted px-1 rounded">lru_cache(1024)</code>.
        </li>
        <li>
          <code className="bg-muted px-1 rounded">funcoes.py</code> — builtins{" "}
          <code className="bg-muted px-1 rounded">SE, MAX, MIN, ABS, ARRED, RUBRICA</code>.
          Placeholders <code className="bg-muted px-1 rounded">FAIXA_IRRF</code> e{" "}
          <code className="bg-muted px-1 rounded">FAIXA_INSS</code> (Onda 2.3).
        </li>
        <li>
          <code className="bg-muted px-1 rounded">contexto.py</code> —{" "}
          <code className="bg-muted px-1 rounded">ContextoFolha(variaveis, rubricas_calculadas)</code>.
        </li>
        <li>
          <code className="bg-muted px-1 rounded">avaliador.py</code> — orquestra:
          compila → monta namespace (Decimal, builtins, RUBRICA, contexto) → eval.
          Mapeia <code className="bg-muted px-1 rounded">NameError</code> e{" "}
          <code className="bg-muted px-1 rounded">DivisionByZero</code> para
          erros tipados com <code className="bg-muted px-1 rounded">code</code> estável.
        </li>
      </ol>
      <h3 className="text-base font-semibold mt-4">Errors com code</h3>
      <ul className="list-disc pl-5 space-y-1 text-xs font-mono">
        <li>FORMULA_SINTAXE</li>
        <li>FORMULA_NAO_PERMITIDA</li>
        <li>FORMULA_FUNCAO_DESCONHECIDA</li>
        <li>FORMULA_VARIAVEL_AUSENTE</li>
        <li>FORMULA_RUBRICA_INEXISTENTE</li>
        <li>FORMULA_DIVISAO_POR_ZERO</li>
        <li>FORMULA_TIPO_INVALIDO</li>
      </ul>
    </Section>
  );
}

function SectionCalculo() {
  return (
    <Section id="calculo" icon={Workflow} title="Cálculo de folha (Onda 2.2)">
      <p>
        <code className="text-xs bg-muted px-1 rounded">
          apps.payroll.services.calculo.calcular_folha(folha) → RelatorioCalculo
        </code>
      </p>
      <h3 className="text-base font-semibold mt-4">Pipeline</h3>
      <ol className="list-decimal pl-5 space-y-1 text-xs">
        <li>
          Carrega <code className="bg-muted px-1 rounded">Rubrica.objects.filter(ativo=True)</code>.
        </li>
        <li>
          Extrai dependências de cada fórmula (
          <code className="bg-muted px-1 rounded">RUBRICA('X')</code>) via análise
          estática AST →{" "}
          <code className="bg-muted px-1 rounded">extrair_dependencias()</code>.
        </li>
        <li>
          Ordena topologicamente com Kahn (tie-breaker alfabético) →{" "}
          <code className="bg-muted px-1 rounded">ordenar_topologicamente()</code>.
          Erros: <code className="bg-muted px-1 rounded">DEPENDENCIA_CICLICA</code>,{" "}
          <code className="bg-muted px-1 rounded">DEPENDENCIA_INEXISTENTE</code>.
        </li>
        <li>
          Carrega vínculos ativos na competência (admitidos antes; não desligados
          antes).
        </li>
        <li>
          Para cada (vínculo, rubrica) em ordem:{" "}
          <code className="bg-muted px-1 rounded">construir_contexto()</code> →{" "}
          <code className="bg-muted px-1 rounded">avaliar()</code> →{" "}
          <code className="bg-muted px-1 rounded">update_or_create(Lancamento)</code>.
        </li>
        <li>
          Limpa lançamentos órfãos (par não tocado nesta execução).
        </li>
        <li>
          Atualiza <code className="bg-muted px-1 rounded">Folha.total_*</code>{" "}
          e status (aberta → calculada).
        </li>
      </ol>
      <Callout variant="info">
        Tudo dentro de{" "}
        <code className="text-xs bg-muted px-1 rounded">transaction.atomic</code>.
        Erros de estrutura abortam tudo; erros de fórmula em par específico viram{" "}
        <code className="text-xs bg-muted px-1 rounded">ErroLancamento</code>{" "}
        no relatório, batch continua.
      </Callout>
    </Section>
  );
}

function SectionTestes() {
  return (
    <Section id="testes" icon={TestTube2} title="Testes (back + front)">
      <h3 className="text-base font-semibold">Backend</h3>
      <pre className="text-[11px] bg-muted px-3 py-2 rounded leading-relaxed overflow-x-auto">
{`cd backend
source .venv/bin/activate
ruff check apps/                              # lint
python manage.py check                        # django
python -m pytest apps/ -q                     # 366 tests, ~50s
python -m pytest --cov=apps --cov-report=term-missing apps/`}
      </pre>

      <h3 className="text-base font-semibold mt-4">Frontend</h3>
      <pre className="text-[11px] bg-muted px-3 py-2 rounded leading-relaxed overflow-x-auto">
{`cd frontend
npm run lint                                  # eslint
npx tsc --noEmit                              # type-check
npx vitest run                                # 10 tests
npm run build                                 # tsc + vite build`}
      </pre>

      <h3 className="text-base font-semibold mt-4">Convenções</h3>
      <ul className="list-disc pl-5 space-y-1 text-xs">
        <li>
          Teste de serviço bate no banco real (sqlite/postgres em conftest); teste
          de view usa <code className="bg-muted px-1 rounded">APIClient</code> com
          token + X-Tenant.
        </li>
        <li>
          Cobertura mínima de fato: <strong>85% das linhas</strong>. Serviços
          críticos (apps/payroll/services, apps/calculo) ≥ 95%.
        </li>
        <li>
          Sem mocks de banco — django-tenants exige conexão real para troca de
          schema funcionar.
        </li>
      </ul>
    </Section>
  );
}

function SectionVersionamento() {
  return (
    <Section id="versionamento" icon={Tag} title="Versionamento (ADR-0010)">
      <p>
        SemVer-ish adaptado ao roadmap: <strong>MAJOR.MINOR.PATCH</strong>.
      </p>
      <ul className="list-disc pl-5 space-y-1 text-xs">
        <li>
          <strong>MAJOR</strong>: piloto em município real (≥ v1.0.0).
        </li>
        <li>
          <strong>MINOR</strong>: onda fechada com escopo novo (ex.: v0.6.0 = Onda
          2.1, v0.7.0 = Onda 2.3).
        </li>
        <li>
          <strong>PATCH</strong>: sub-onda dentro de onda (ex.: v0.6.1 = Onda 2.2 em
          cima da 2.1), bugfix.
        </li>
        <li>
          Todas as tags são <strong>anotadas</strong> (
          <code className="bg-muted px-1 rounded">git tag -a vX.Y.Z -m &quot;…&quot;</code>).
        </li>
        <li>
          Docs-only changes <strong>não</strong> incrementam versão.
        </li>
      </ul>
      <Callout variant="warning">
        Nunca rodar <code className="text-xs bg-muted px-1 rounded">--no-verify</code>{" "}
        nem desabilitar hook. Se um hook falha, corrija a causa raiz.
      </Callout>
    </Section>
  );
}

function SectionValidacao() {
  return (
    <Section id="validacao" icon={Activity} title="Rotina de validação integral">
      <p>
        Aplicada antes de toda atualização ir pro ar. Registrada como entrada{" "}
        <code className="text-xs bg-muted px-1 rounded">tipo: &quot;validacao&quot;</code>{" "}
        no <code className="text-xs bg-muted px-1 rounded">status.json</code>.
      </p>
      <ol className="list-decimal pl-5 space-y-2 text-xs">
        <li>
          <strong>Backend lint:</strong>{" "}
          <code className="bg-muted px-1 rounded">ruff check apps/</code> → 0 erros.
        </li>
        <li>
          <strong>Backend check:</strong>{" "}
          <code className="bg-muted px-1 rounded">python manage.py check</code> + sem
          migrations pendentes.
        </li>
        <li>
          <strong>Backend testes:</strong>{" "}
          <code className="bg-muted px-1 rounded">pytest apps/ --cov</code> → todos
          verde, cobertura ≥ 85%.
        </li>
        <li>
          <strong>Frontend lint + types:</strong>{" "}
          <code className="bg-muted px-1 rounded">npm run lint</code> +{" "}
          <code className="bg-muted px-1 rounded">npx tsc --noEmit</code>.
        </li>
        <li>
          <strong>Frontend testes + build:</strong>{" "}
          <code className="bg-muted px-1 rounded">npx vitest run</code> +{" "}
          <code className="bg-muted px-1 rounded">npm run build</code>.
        </li>
        <li>
          <strong>E2E smoke via API:</strong> login → tenant → cadastros → admissão →
          rubrica → folha → calcular → recalcular (idempotência).
        </li>
        <li>
          <strong>Visual:</strong> screenshot headless (
          <code className="bg-muted px-1 rounded">google-chrome --headless --screenshot=…</code>)
          das telas críticas + página de status pública.
        </li>
        <li>
          <strong>Registrar:</strong> entrada{" "}
          <code className="bg-muted px-1 rounded">validacao</code> no{" "}
          <code className="bg-muted px-1 rounded">status.json</code> com resumo
          executivo + detalhe técnico.
        </li>
      </ol>
    </Section>
  );
}

function SectionNovaOnda() {
  return (
    <Section id="nova-onda" icon={GitBranch} title="Como entregar uma onda nova">
      <ol className="list-decimal pl-5 space-y-2 text-xs">
        <li>
          <strong>Planejar</strong>: ADR se houver decisão estrutural; senão, escopo
          claro no roadmap.
        </li>
        <li>
          <strong>Implementar</strong> backend → testes → frontend (quando
          aplicável).
        </li>
        <li>
          <strong>Rodar a rotina de validação</strong> (seção acima) — 100% verde
          obrigatório.
        </li>
        <li>
          <strong>Atualizar guias</strong>:
          <ul className="list-disc pl-5 mt-1 space-y-0.5">
            <li>
              <code className="bg-muted px-1 rounded">CHANGELOG.md</code> — entrada
              completa (o quê / por quê / impacto / próximos passos).
            </li>
            <li>
              <code className="bg-muted px-1 rounded">status-page/status.json</code> — atualiza
              progresso do bloco + adiciona entrada no changelog com{" "}
              <code className="bg-muted px-1 rounded">resumo_executivo</code>.
            </li>
            <li>
              <code className="bg-muted px-1 rounded">frontend/src/pages/GuiaPage.tsx</code> — atualiza{" "}
              <code className="bg-muted px-1 rounded">LAST_UPDATED</code> e
              seções afetadas.
            </li>
            <li>
              <strong>Este guia</strong> (
              <code className="bg-muted px-1 rounded">GuiaAdminPage.tsx</code>) —
              novas pastas, novos serviços, novos códigos de erro, novos endpoints.
            </li>
            <li>
              <code className="bg-muted px-1 rounded">docs/ROADMAP.md</code> — marca
              onda como concluída.
            </li>
          </ul>
        </li>
        <li>
          <strong>Commit</strong>: 1 commit por onda, mensagem clara, Co-Authored-By
          quando trabalhar com Claude.
        </li>
        <li>
          <strong>Tag</strong>:{" "}
          <code className="bg-muted px-1 rounded">git tag -a v0.X.Y -m &quot;Onda X.Y — título&quot;</code>.
        </li>
        <li>
          <strong>Push</strong> → workflow{" "}
          <code className="bg-muted px-1 rounded">status-page.yml</code> dispara
          deploy automático do GitHub Pages.
        </li>
      </ol>
    </Section>
  );
}

function SectionManterGuias() {
  return (
    <Section id="manter-guias" icon={Map} title="Manter os guias atualizados">
      <div className="grid gap-3 sm:grid-cols-2">
        <GuiaCard
          title="/guia (usuário)"
          desc="Operadores das prefeituras. Fluxos, atalhos, restrições por papel, o que tá disponível e o que tá em construção. Sem jargão técnico."
          quando="Toda onda que muda algo visível ao operador (tela nova, fluxo, permissão)."
          onde="frontend/src/pages/GuiaPage.tsx"
        />
        <GuiaCard
          title="/guia-admin (desenvolvedor)"
          desc="Você (que desenvolve). Arquitetura, pipelines, código, política de versionamento, rotina de validação."
          quando="Toda mudança estrutural (pasta, serviço, ADR, código de erro novo)."
          onde="frontend/src/pages/GuiaAdminPage.tsx"
        />
        <GuiaCard
          title="Status page (público)"
          desc="Stakeholders externos (doutor, parceiros, futuros clientes). Resumo executivo de cada onda + roadmap."
          quando="Toda onda + toda validação integral."
          onde="status-page/status.json"
        />
        <GuiaCard
          title="CHANGELOG.md"
          desc="Memória técnica do projeto. Toda alteração relevante."
          quando="Toda onda. Toda mudança que afeta contrato, schema ou semântica."
          onde="CHANGELOG.md (raiz)"
        />
      </div>
    </Section>
  );
}

function SectionDocs() {
  return (
    <Section id="docs" icon={FileText} title="Mapa de documentos">
      <ul className="list-disc pl-5 space-y-1 text-xs">
        <li>
          <code className="bg-muted px-1 rounded">docs/ROADMAP.md</code> — Blocos
          0–7 com escopo e critério de aceitação.
        </li>
        <li>
          <code className="bg-muted px-1 rounded">docs/ARCHITECTURE.md</code> —
          visão macro.
        </li>
        <li>
          <code className="bg-muted px-1 rounded">docs/MULTI_TENANT_PLAYBOOK.md</code> —
          como adicionar feature respeitando o tenant.
        </li>
        <li>
          <code className="bg-muted px-1 rounded">docs/adr/</code> — decisões
          versionadas:
          <ul className="list-disc pl-5 mt-1 space-y-0.5">
            <li>0010 — política de versionamento</li>
            <li>0011 — adaptadores externos configuráveis</li>
            <li>0012 — DSL via Python AST whitelist</li>
          </ul>
        </li>
        <li>
          <code className="bg-muted px-1 rounded">docs/leiautes/manad/</code> —
          layout MANAD (Bloco 4).
        </li>
        <li>
          <code className="bg-muted px-1 rounded">docs/relatorios/</code> — HTML dos
          quinzenais publicados.
        </li>
      </ul>
    </Section>
  );
}

function SectionAmbientes() {
  return (
    <Section id="ambientes" icon={Server} title="Ambientes & deploy">
      <ul className="list-disc pl-5 space-y-1 text-xs">
        <li>
          <strong>Local</strong>: backend 8000, frontend 5173. Banco Postgres no
          host (não containerizado por enquanto).
        </li>
        <li>
          <strong>CI</strong>: GitHub Actions (
          <code className="bg-muted px-1 rounded">backend-ci.yml</code>,{" "}
          <code className="bg-muted px-1 rounded">frontend-ci.yml</code>) roda lint
          + testes a cada PR/push.
        </li>
        <li>
          <strong>Status page</strong>: GitHub Pages, deploy automático via{" "}
          <code className="bg-muted px-1 rounded">status-page.yml</code> quando algo
          em <code className="bg-muted px-1 rounded">status-page/**</code> muda.
          URL pública:{" "}
          <a
            href="https://darlanvelozo.github.io/Arminda_Software/"
            target="_blank"
            rel="noreferrer"
            className="underline"
          >
            darlanvelozo.github.io/Arminda_Software
          </a>
          .
        </li>
        <li>
          <strong>Produção (futura)</strong>: definida no Bloco 6 (operação piloto).
          Provavelmente container + Postgres gerenciado + Caddy/Nginx.
        </li>
      </ul>
    </Section>
  );
}

function SectionMemoria() {
  return (
    <Section id="memoria" icon={HardDrive} title="Memória do Claude">
      <p>
        Memórias persistentes do Claude Code ficam em{" "}
        <code className="text-xs bg-muted px-1 rounded">
          ~/.claude/projects/-home-darlan-projetos-github-arminda/memory/
        </code>{" "}
        e cobrem:
      </p>
      <ul className="list-disc pl-5 space-y-1 text-xs">
        <li>
          <strong>user</strong>: papel, preferências, contexto.
        </li>
        <li>
          <strong>feedback</strong>: regras que vieram de correções ou de
          aprovações explícitas (ex.: &quot;sempre commitar a cada versão&quot;,
          &quot;tags anotadas&quot;).
        </li>
        <li>
          <strong>project</strong>: estado, decisões em andamento, marcos.
        </li>
        <li>
          <strong>reference</strong>: ponteiros pra sistemas externos (Linear,
          Grafana etc.).
        </li>
      </ul>
      <Callout variant="info">
        Não armazena código, git history, schema — pra isso o próprio repo é
        autoritativo. Memória é só o que não dá pra recuperar lendo o projeto.
      </Callout>
    </Section>
  );
}

// ============================================================
// Componentes auxiliares
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

function TechCard({ title, items }: { title: string; items: string[] }) {
  return (
    <Card>
      <CardContent className="py-4 space-y-2">
        <div className="flex items-center gap-2 font-medium text-sm">
          <Package className="h-4 w-4 text-muted-foreground" />
          {title}
        </div>
        <ul className="text-xs text-muted-foreground space-y-1">
          {items.map((it) => (
            <li key={it} className="flex items-start gap-1.5">
              <Code2 className="h-3 w-3 mt-0.5 text-primary shrink-0" />
              <span>{it}</span>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}

function GuiaCard({
  title,
  desc,
  quando,
  onde,
}: {
  title: string;
  desc: string;
  quando: string;
  onde: string;
}) {
  return (
    <Card>
      <CardContent className="py-4 space-y-2">
        <div className="font-medium text-sm">{title}</div>
        <p className="text-xs text-muted-foreground">{desc}</p>
        <div className="text-xs text-muted-foreground">
          <strong>Atualizar quando:</strong> {quando}
        </div>
        <div className="text-xs">
          <code className="bg-muted px-1 rounded">{onde}</code>
        </div>
      </CardContent>
    </Card>
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
  const Icon = { info: Info, warning: Activity, tip: Lightbulb }[variant];
  return (
    <div className={`flex gap-2.5 rounded-md border p-3 text-xs ${styles}`}>
      <Icon className="h-4 w-4 shrink-0 mt-0.5" />
      <div className="leading-relaxed">{children}</div>
    </div>
  );
}

function formatDate(iso: string): string {
  const [y, m, d] = iso.split("-");
  return `${d}/${m}/${y}`;
}
