# ADR-0019 — Folha complementar: lançamentos explícitos por servidor

**Status:** Aceita · 2026-06-15 · Vigora para Bloco 3 (Onda 3.5)

## Contexto

Quinta e última onda do Bloco 3. A **folha complementar** é uma folha
adicional para uma competência que já teve a folha mensal processada. Serve
para pagar **diferenças** que ficaram de fora ou foram apuradas depois:

- reajuste retroativo aplicado após o fechamento da folha mensal;
- rubrica esquecida ou corrigida;
- diferença de provento por erro de cadastro.

Há duas perguntas de escopo que mudam o modelo de dados (decididas com o
usuário):

1. **O que dispara os valores?** — _manual agora, recálculo automático
   (delta) depois._
2. **Como tratar INSS/IRRF?** — _escolher a melhor forma deixando abertura
   para evoluir._

Sobre incidências, o ponto técnico é que **INSS e IRRF são cumulativos no
mês**: o INSS tem teto e o IRRF é progressivo por faixa. Calcular a
incidência do complemento **isoladamente** (sobre o próprio valor, sem olhar
a folha mensal da competência) produz **faixa de IRRF e teto de INSS
errados** quando somado ao que já foi pago no mês — ou seja, é *ativamente
incorreto* no caso comum. A forma correta exige considerar a base já
tributada na folha mensal de origem (modo **acumulado**), o que é mais
complexo e depende de vincular o complementar à mensal.

## Decisão

Entregar o complementar **v1 por lançamentos explícitos**, sem incidência
automática, e deixar o gancho para o modo acumulado:

1. **Reusa** `TipoFolha.COMPLEMENTAR` (já existente no enum).

2. **Programação por itens** (mesmo padrão de férias/licença-prêmio): modelo
   `ComplementarItem(folha, vinculo, rubrica, valor)`, único por
   folha+vínculo+rubrica. O operador escolhe o servidor, a rubrica (provento
   **ou** desconto) e informa o **valor explícito**.

3. **Cálculo:** para folhas `COMPLEMENTAR`, o engine **não roda fórmulas** —
   materializa cada item como um `Lancamento` com o valor informado e soma
   proventos/descontos pelo `tipo` da rubrica. **Sem incidência automática:**
   se houver INSS/IRRF complementar devido, o operador lança explicitamente
   (nunca erra faixa/teto). Vínculos da folha = os que têm itens.

4. **Gancho para evolução** (`folha_origem`): novo FK opcional
   `Folha.folha_origem` (self-FK, `null=True`), apontando para a folha mensal
   da mesma competência. No v1 é só **rastreabilidade**; uma onda futura usa
   esse vínculo para o **modo acumulado** (recálculo delta + incidência sobre
   a base do mês) sem migration quebrada.

## Por que não incidência automática isolada

Entre as três opções consideradas:

- **Isolada** (incidência sobre o próprio complemento): simples, mas *errada*
  no caso comum (faixa de IRRF / teto de INSS). Descartada.
- **Acumulada** (considerando a base da mensal): correta, porém exige o
  vínculo `folha_origem` + somatório de bases. Fica para onda futura.
- **Explícita/manual** (escolhida): nunca erra (o valor é informado), entrega
  o caso de uso real (pequenos ajustes), e deixa o caminho mais limpo para o
  modo acumulado. É o melhor v1 correto-o-suficiente.

## Consequências

### Positivas
- Reusa o padrão de itens-na-folha e o `_limpar_orfaos_e_fechar`; pouco
  código novo no engine (um ramo dedicado, sem fórmulas).
- Fecha o Bloco 3 (folhas especiais) sem introduzir cálculo tributário de
  risco.
- `folha_origem` documenta a costura para o modo acumulado.

### Custos / dívidas
- Incidência do complemento é responsabilidade do operador no v1.
- O recálculo automático (delta) e o modo acumulado ficam mapeados para uma
  onda futura (Bloco 2.x de paridade ou um bloco de folha avançada).

## Alternativas descartadas

- **Recálculo automático já no v1:** exige snapshot da mensal e comparação
  verba a verba; alto custo, fora do escopo de fechar o Bloco 3.
- **Incidência isolada automática:** incorreta (ver acima).
