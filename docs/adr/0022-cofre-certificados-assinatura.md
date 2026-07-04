# ADR-0022 — Cofre de certificados digitais + assinatura XML-DSig

**Status:** Aceita · 2026-07-03 · Vigora para Bloco 4 (Onda 4.2)

## Contexto

O eSocial (e qualquer integração com a Receita) exige assinar os eventos com o
**certificado digital e-CNPJ (ICP-Brasil)** do órgão. A Onda 4.1 gerou e validou
o XML; falta **guardar o certificado com segurança** e **assinar** (XML-DSig).

Um cliente forneceu um **A1 real** (e-CNPJ da Prefeitura de Brejo) para testes de
integração. Isso torna a onda concreta: dá para construir e provar o cofre e a
assinatura contra um certificado verdadeiro, no ambiente de teste.

Restrições de segurança que guiam o desenho:
- O `.pfx` e a senha são **credenciais sensíveis** — nunca em git, nunca em log,
  nunca devolvidos por API, e **cifrados em repouso** no banco.
- Assinar/transmitir como um ente público é ação de mundo real — a transmissão
  só ocorre com autorização explícita e contra **homologação** (produção
  restrita), nunca no automático.

## Decisão

1. **Cofre no banco, cifrado.** Modelo `CertificadoDigital` (app `esocial`),
   **um por `OrgaoEmissor`** (`OneToOne`). Guarda o `.pfx` e a senha **cifrados
   com Fernet** (AES-128 autenticado), mais **metadados em claro** para
   operação: titular, CNPJ, emissor (AC), `validade_inicio`/`fim`, thumbprint.
   - A chave Fernet vem de `settings.ESOCIAL_CERT_KEY` (**env**, segredo real em
     produção; default só para dev). A chave **não** fica no banco — quem tem o
     dump não decifra sem a chave.
   - Sem `simple-history` neste modelo (não versionar blobs de segredo).

2. **Serviço `cofre`** — `guardar_certificado(orgao, pfx, senha)` valida (abre o
   PKCS#12, confere validade), extrai metadados, cifra e faz upsert.
   `carregar_material(cert)` decifra e devolve (chave privada, cert, cadeia) —
   uso **interno** (assinatura), jamais exposto.

3. **Serviço `assinatura`** — `assinar_evento(evento)` assina o XML do evento
   com **XML-DSig enveloped** (padrão eSocial: `Reference URI=""`, transformas
   enveloped-signature + C14N, `RSA-SHA256`/`SHA256`), via `signxml`. A
   `<Signature>` entra como último filho de `<eSocial>` (o que o XSD exige). O
   evento passa a `status=assinado`; o XML assinado agora valida contra o **XSD
   completo** (a assinatura deixa de ser relaxada — fecha o gancho da 4.1).

4. **Escopo da 4.2:** cofre (upload/validar/guardar) + assinatura + validação do
   XML assinado. **Não** transmite ainda (próxima onda), nem toca em serviços da
   Receita (canal a definir — ADR-0021/Bloco 10).

## Consequências

### Positivas
- Certificado protegido (cifrado em repouso, fora do git, sem exposição por API).
- Assinatura real destrava a transmissão e valida contra o XSD oficial completo.
- Fundação comum ao eSocial e à futura integração com a Receita.

### Custos / riscos
- **Gestão da chave Fernet**: se a `ESOCIAL_CERT_KEY` vazar, os certificados
  ficam expostos; se for perdida, os certificados guardados tornam-se ilegíveis.
  Guardar como segredo de produção (env), com rotação planejada.
- Dependências novas: `cryptography`, `signxml` (`pip install -r requirements`).
- A senha de um `.pfx` recebida em texto puro (fora do sistema) deve ser tratada
  como sensível pelo cliente; recomendável reemitir se trafegou exposta.

## Alternativas descartadas
- **Guardar o `.pfx` em disco/volume** em vez de cifrado no banco: pior para
  multi-tenant e backup; o cofre cifrado viaja com o schema do tenant.
- **python-xmlsec** (libxmlsec1): exige lib de sistema; `signxml` é mais
  portável (só `cryptography` + `lxml`).
