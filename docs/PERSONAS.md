# Personas e jornadas no Arminda

> Quem usa o sistema, em qual bloco do roadmap ele aparece e o que ganha
> em cada etapa. Mantém junto a foto técnica (papel RBAC) e a foto de
> negócio (jornada operacional).
>
> Atualizado: 2026-05-27. Referência cruzada com [ROADMAP.md](ROADMAP.md)
> e [ADR-0007 (JWT/RBAC)](adr/0007-jwt-rbac.md).

---

## Princípios

1. **Persona ≠ papel RBAC.** Persona é a pessoa real ("o contador da
   Prefeitura de Brejo"). Papel é a marcação técnica que dá ou tira
   permissão (`contador_municipio`). Uma pessoa pode acumular papéis;
   um papel pode atender várias personas.
2. **Toda feature do roadmap tem dono.** Quando uma feature entra num
   bloco, este documento deve apontar qual persona ganha e o que muda
   no dia dela.
3. **Papel novo exige migração.** Adicionar `gestor_municipio` significa
   criar `Group` no schema `public`, dar permissions DRF aderentes,
   criar tela de atribuição, atualizar testes. Não é trivial — só
   adicionar quando o bloco que precisa entrar em desenvolvimento.

---

## Personas reconhecidas

### 1. RH municipal (operador principal)
- **Quem é:** servidor concursado ou comissionado da Secretaria de
  Administração ou de RH, geralmente 1-3 pessoas no município.
- **Conhece:** legislação trabalhista municipal, processos de admissão,
  desligamento, férias, eSocial. Usa o sistema diariamente.
- **Não conhece:** SQL, programação, jargão técnico. Trabalha por tela.
- **Papel RBAC:** `rh_municipio`.
- **Entra:** desde o Bloco 1.
- **Tarefas críticas:** admitir, desligar, transferir, completar
  cadastros pré-eSocial, conferir folha, gerar relatórios.

### 2. Administrador do município
- **Quem é:** secretário de administração ou chefe de gabinete que
  delega operação para RH e Financeiro, mas precisa ter visão total.
- **Conhece:** todo o sistema, mas em modo "supervisão".
- **Papel RBAC:** `admin_municipio`.
- **Entra:** desde o Bloco 1.
- **Tarefas críticas:** atribuir papéis a usuários, configurar
  integrações externas (Bloco 5), aprovar mudanças sensíveis.

### 3. Financeiro / Folha (operador de pagamento)
- **Quem é:** contador ou auxiliar do setor financeiro responsável
  por fechar a folha e gerar pagamento.
- **Conhece:** cálculo de folha, tabelas legais, conciliação.
- **Papel RBAC atual:** `financeiro_municipio`.
- **Limitação:** hoje mistura folha + tesouraria + contábil. No Bloco
  9 vai se dividir com o `contador_municipio`.
- **Entra:** com força no Bloco 2 (cálculo da folha).

### 4. Contador (escopo contábil) — **papel novo**
- **Quem é:** responsável pelo registro contábil dos atos da folha
  (empenho, liquidação, pagamento), integração com sistema contábil
  do município (PCASP), RREO/RGF e cumprimento da LRF.
- **Por que separar do financeiro:** competências distintas. O
  financeiro fecha a folha; o contador empenha, paga, presta contas
  e responde ao TCE pelo limite de gasto com pessoal.
- **Papel RBAC:** `contador_municipio` (a criar — Bloco 9).
- **Entra:** Bloco 9 (Tesouraria, contábil e LRF).
- **Tarefas críticas:** gerar CNAB 240, conciliar com banco, registrar
  PCASP, montar RREO/RGF, monitorar painel LRF.

### 5. Gestor do município (prefeito / secretários) — **papel novo**
- **Quem é:** prefeito, secretários e chefe de gabinete. Não opera
  o sistema; consome indicadores.
- **Conhece:** o município como um todo, com olhar estratégico.
- **Papel RBAC:** `gestor_municipio` (a criar — Bloco 7).
- **Recorte por secretaria:** secretário de Saúde só vê os indicadores
  da SEMSA, não a folha inteira. O sistema precisa modelar isso via
  `UsuarioMunicipioPapel` × `Lotacao` (ou `Natureza`).
- **Entra:** Bloco 7 (Dashboards e BI) com força; antecipa parcial no
  Bloco 9 (painel LRF para o prefeito).
- **Tarefas críticas:** dashboard de KPIs, simulação de cenários,
  aprovação de atos sensíveis (admissão de comissionado, ato de
  exoneração), assinatura digital (Bloco 10).

### 6. Controle interno / Auditor — **papel novo**
- **Quem é:** servidor da Controladoria Geral do Município ou
  Procuradoria, responsável por garantir conformidade.
- **Conhece:** legislação, processos, riscos. Trabalha por auditoria
  retroativa, não por operação diária.
- **Papel RBAC:** `controle_interno_municipio` (a criar — Bloco 10).
- **Diferença para `leitura_municipio`:** este só lê dados de domínio;
  o controle interno acessa **logs, histórico completo, auditoria**
  (incluindo quem acessou o quê e quando), assina pareceres,
  pode bloquear operações suspeitas.
- **Entra:** Bloco 10 (Compliance e auditoria).

### 7. Servidor final (autoatendimento) — **papel novo / vínculo direto**
- **Quem é:** o próprio servidor da prefeitura, consumindo seus
  próprios dados.
- **Acesso:** só os dados dele. Modelagem diferente — não é "papel"
  global, é vínculo `Usuario` ↔ `Servidor` 1:1.
- **Papel RBAC:** `servidor_final` (a criar — Bloco 7).
- **Entra:** Bloco 7 (Portal do servidor) e ganha mais no Bloco 8
  (férias, atestados, declarações) e Bloco 10 (contracheque com
  assinatura digital).
- **Tarefas críticas:** consultar contracheque, pedir férias, enviar
  atestado, atualizar dados pessoais, baixar declaração para imposto.

### 8. Staff Arminda (equipe interna do produto)
- **Quem é:** equipe de desenvolvimento e suporte do produto.
- **Acesso:** cross-tenant via management commands e admin Django.
- **Papel RBAC:** `staff_arminda`.
- **Não tem jornada de produto.** É papel de suporte.

### 9. Fiscal externo / cidadão (Portal da Transparência) — **anônimo**
- **Quem é:** qualquer cidadão, jornalista, fiscal do TCE/CGU.
- **Acesso:** anônimo (sem login). Consome a página pública de
  transparência.
- **Não tem papel RBAC.** É leitor anônimo.
- **Entra:** Bloco 10 (Portal da Transparência).

---

## Matriz Persona × Bloco

Marcador:
- 🟢 = ganha capacidade nova nesse bloco
- 🔧 = manutenção/refinamento do que já tem
- — = não impactado

| Persona / Papel | B1 | B2 | B3 | B4 | B5 | B6 | B7 | B8 | B9 | B10 |
|---|---|---|---|---|---|---|---|---|---|---|
| **RH municipal** (`rh_municipio`) | 🟢 cadastros, admissão, desligamento, transferência, vínculos | 🟢 ver folha calculada | 🟢 13º, férias, rescisão | 🟢 status eSocial | 🔧 — | 🔧 — | 🔧 — | 🟢 probatório, progressão, frequência, férias planejada, saúde, aposent./pensão | — | 🟢 LGPD ops |
| **Admin do município** (`admin_municipio`) | 🟢 gestão de usuários, papéis | 🔧 | 🔧 | 🟢 config integrações externas | 🟢 config TCE | 🔧 | 🟢 atribuir gestor | 🟢 atribuir papéis ao Bloco 8 | 🟢 atribuir contador | 🟢 atribuir controle interno |
| **Financeiro/Folha** (`financeiro_municipio`) | 🔧 | 🟢 criar folha, calcular, fechar | 🟢 calcular 13º, férias, rescisão | 🟢 conferir eSocial vs folha | 🔧 conferir TCE | 🟢 piloto: validar paridade | 🔧 alertas IA na folha | — | 🔧 separa escopo do contador | 🔧 |
| **Contador** (`contador_municipio` — novo) | — | — | — | — | — | — | — | — | 🟢 **estreia: CNAB, RREO/RGF, PCASP, conciliação, LRF, retroativo** | 🟢 certificado digital |
| **Gestor** (`gestor_municipio` — novo) | — | — | — | — | — | 🟢 leitura de KPIs do piloto | 🟢 **estreia: dashboards, BI, alertas IA, simulação** | 🔧 KPIs de pessoal | 🟢 painel LRF, alerta de aproximação de limite | 🟢 assinatura digital de atos |
| **Controle interno** (`controle_interno_municipio` — novo) | — | — | — | — | — | — | — | — | — | 🟢 **estreia: auditoria UI, logs de acesso, parecer técnico, retenção LGPD** |
| **Servidor final** (`servidor_final` — novo) | — | — | — | — | — | — | 🟢 **estreia: portal PWA, contracheque, declarações, dados pessoais** | 🟢 pedir férias, enviar atestado, agendar perícia | — | 🟢 contracheque com assinatura digital, exclusão LGPD sob demanda |
| **Leitura** (`leitura_municipio`) | 🟢 ver cadastros, dashboards básicos | 🔧 | 🔧 | 🔧 | 🔧 | 🔧 | 🔧 | 🔧 | 🔧 | 🔧 |
| **Staff Arminda** (`staff_arminda`) | 🟢 management commands, admin Django, importador SIP | 🔧 | 🔧 | 🔧 | 🔧 | 🔧 piloto: suporte intenso | 🔧 | 🔧 | 🔧 | 🔧 |
| **Cidadão / fiscal externo** (anônimo) | — | — | — | — | — | — | — | — | — | 🟢 **estreia: Portal da Transparência (Lei 12.527)** |

---

## Resumo dos papéis RBAC novos a criar

| Papel | Bloco | Implementação técnica |
|---|---|---|
| `gestor_municipio` | Bloco 7 | Group + permissions (read em quase tudo + write em ato administrativo); recorte por `Lotacao` ou `NaturezaLotacao` via subset de `UsuarioMunicipioPapel`. |
| `contador_municipio` | Bloco 9 | Group + permissions específicas para `apps.tesouraria` (a criar) e leitura de `apps.payroll`. Não tem write em `Servidor`/`VinculoFuncional`. |
| `controle_interno_municipio` | Bloco 10 | Group + permissions de read em tudo + write em `Parecer` e `LogAuditoria`. Recebe registros de acesso via signal. |
| `servidor_final` | Bloco 7 | Modelagem diferente: `Usuario.servidor_vinculado = FK(Servidor)`. Permissions custom que filtram queryset por `request.user.servidor_vinculado`. Não é Group global. |

Toda mudança vira ADR (`docs/adr/0013-*` em diante) antes de virar
migration.

---

## Como manter este documento

- **Cada onda nova:** se a entrega muda a jornada de uma persona,
  marca na matriz com 🟢 ou 🔧.
- **Cada papel RBAC novo:** atualiza a tabela de papéis e cria ADR.
- **Cada bloco que entra em desenvolvimento:** revisar a coluna do
  bloco e confirmar quais personas são afetadas (evita esquecer
  persona quando o escopo se ajusta).

Quando o frontend ganha uma tela nova, o desenvolvedor deve
perguntar: "qual papel acessa? qual persona usa?" e atualizar este
documento se for inconsistente com o que já está aqui.
