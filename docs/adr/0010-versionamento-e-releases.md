# ADR-0010 — Estratégia de versionamento e releases

**Status:** Aceita · 2026-05-08 · Vigora a partir da próxima release

## Contexto

O projeto Arminda é entregue por **blocos sequenciais** (0 a 7) divididos em
**ondas** numeradas (ex.: 1.3a, 1.3b, 1.3c, 1.5b). Cada onda costuma fechar
em poucos dias e gera um marco visível. Em paralelo, fixes e refatorações
internas acontecem entre ondas.

Até a release `v0.5.1` o esquema de versionamento foi montado de forma
empírica — funcionou, mas dependia da memória de quem estava tagueando.
Esta ADR consolida a regra para que toda release futura siga a mesma
política, e para que o histórico fique navegável anos depois.

### Não-objetivos

- Adotar SemVer **estrito** com versionamento de API antes de o produto
  ter API estável publicada para terceiros (isso só faz sentido no
  Bloco 7).
- Releases trimestrais com freeze code — o projeto tem entregas
  contínuas, não cabe ciclo formal de planejamento de release.

## Decisão

### 1. Esquema: SemVer adaptado a blocos

Versão = `MAJOR.MINOR.PATCH` onde:

| Componente | O que representa |
|---|---|
| **MAJOR** | Marco de produto. Hoje permanece `0` enquanto estamos pré-piloto. Vira `1` quando a folha calcular em produção (fim do Bloco 2). Vira `2` quando o piloto encerrar com sucesso (Bloco 6). |
| **MINOR** | Avanço de bloco/onda do roadmap. Cada bloco principal incrementa MINOR. **Ondas que fechem um sub-marco também incrementam MINOR.** |
| **PATCH** | Correções, polimentos, hotfixes e melhorias dentro da mesma onda — não muda o conjunto de funcionalidades visíveis. |

### 2. Mapeamento bloco/onda → versão (referência)

| Bloco/Onda | Versão |
|---|---|
| Bloco 0 (estrutura inicial) | `v0.0.0` |
| Bloco 1.1 (fundação multi-tenant + auth) | `v0.1.0` |
| Bloco 1.2 (cadastros + serviços RH) | `v0.2.0` |
| Bloco 1.3a + 1.3a-bis (frontend autenticado) | `v0.3.0` |
| Bloco 1.3b (telas de domínio) | `v0.3.1` |
| Bloco 1.3c (ciclo de vida + lazy routes) | `v0.3.2` |
| Bloco 1.4 (importador Fiorilli SIP) | `v0.4.0` |
| Bloco 1 — Onda 1.5 (Documentos/Configurações/⌘K) | `v0.5.0` |
| Bloco 1 — Onda 1.5b (organização por vínculo+área) | `v0.5.1` |
| **Próximas:** | |
| Onda 1.4-bis (importador estendido — DEPDESPESA) | `v0.5.2` *(patch, polimento do importador)* |
| Bloco 2 — Onda 2.1 (DSL de fórmulas) | `v0.6.0` |
| Bloco 2 completo (folha mensal calculando) | **`v1.0.0`** — primeiro release "operacional" |
| Bloco 3 (folhas especiais) | `v1.1.0` |
| Bloco 4 (obrigações federais) | `v1.2.0` |
| Bloco 5 (TCE-MA) | `v1.3.0` |
| Bloco 6 (piloto encerrado com sucesso) | **`v2.0.0`** |
| Bloco 7 (diferenciação) | `v2.1.0` em diante |

**Regra prática:**
- Onda principal que adiciona feature visível → MINOR.
- Onda de extensão/polimento dentro do mesmo escopo → PATCH (mas pode virar MINOR se a entrega ficar grande — vide v0.5.1).
- Fechamento de bloco completo → MINOR (ou MAJOR em casos especiais: v1.0.0, v2.0.0).

### 3. Tags Git

Toda tag é **anotada** (`git tag -a`), nunca leve. A mensagem da tag deve:

1. Linha 1: título da entrega ("Bloco 1.4 — Importador Fiorilli SIP").
2. Linha vazia.
3. Parágrafo curto (3-5 linhas) descrevendo o que entra com aquela versão.
4. Linha final identificando o bloco/onda do roadmap.

**Exemplo:**
```bash
git tag -a v0.4.0 6d361b9 -m "Bloco 1.4 — Importador Fiorilli SIP (Firebird → Postgres)

Pipeline ETL unidirecional do banco legado SIP.FDB para o schema do
município no Postgres. 3 camadas: extract (adapters.firebird),
transform (services.mapping — funções puras) e load (loaders).
Smoke E2E contra FDB real: 91/91 cargos, 66/66 lotações, 517/517 servidores.

Bloco 1, Onda 1.4."
```

### 4. Quando criar a tag

A tag é criada **após** o commit que fecha a onda e **antes** do próximo trabalho começar. Sequência:

1. Commit final da onda em `main` (CI verde).
2. CHANGELOG.md atualizado com a entrada estruturada da onda.
3. Status-page (`status.json`) atualizado com o progresso e changelog.
4. GuiaPage (frontend) atualizado se a feature mudou o que o usuário vê.
5. **Criar tag anotada** com a mensagem padronizada.
6. Push: `git push origin main && git push origin <nova-tag>`.

### 5. PATCH em release anterior (back-port)

Se aparecer bug crítico em produção depois que MINOR já avançou, **não** voltamos para uma branch antiga. Subimos um PATCH na versão corrente. Isso evita branches de manutenção paralelas que ninguém quer manter sozinho.

Exceção: depois do Bloco 6 (piloto operando em município real), pode ser necessário branch de manutenção `release/v1.x` paralela ao desenvolvimento de `v2.x`. Decidir naquele momento.

### 6. Pre-releases e snapshots

Não usar `-rc`, `-beta`, `-alpha` no momento. O projeto está em pré-piloto;
toda release é interna. Quando o piloto começar (Bloco 6), reavaliar.

### 7. Relação versão × CHANGELOG × status.json × Relatório quinzenal

| Documento | Granularidade | Atualizado quando |
|---|---|---|
| **Tag Git** | Por onda/bloco | Ao final da onda |
| **CHANGELOG.md** | Por onda + por marco interno | A cada commit relevante |
| **status.json** | Bloco/onda visíveis ao stakeholder | A cada onda fechada |
| **GuiaPage** | Feature visível ao usuário operador | A cada onda que afeta UX |
| **Relatório quinzenal** | Resumo executivo agregando 2 semanas | A cada 15 dias |

Os quatro documentos contam a mesma história em granularidades diferentes — não duplicam, complementam.

## Consequências

### Positivas

- Toda release tem **regra escrita**, não depende de memória.
- O mapeamento bloco → versão deixa o histórico do projeto **navegável anos depois** — qualquer dev vê uma tag e sabe a que momento do roadmap ela corresponde.
- Política de PATCH na corrente (vs. back-port em branch) evita armadilha clássica de projeto solo.
- `v1.0.0` significa algo concreto: "folha calcula" — não é arbitrário.

### Negativas / trade-offs

- O esquema mistura SemVer com semântica de produto (blocos). Pode confundir devs externos acostumados a SemVer estrito. Mitigação: a ADR é a referência oficial; toda dúvida resolve aqui.
- Quando o projeto adquirir API pública (Bloco 7), pode ser necessário separar **versionamento do produto** (continua atrelado a blocos) de **versionamento da API** (SemVer estrito por endpoint, via headers ou prefixos `/v1/`). Decisão futura.

## Histórico

- 2026-05-08 — Aceita. Tags `v0.0.0` a `v0.5.1` já estavam em uso e
  ficam preservadas como histórico válido.
