# apps/imports — Contexto

> App responsável pela importação de dados de sistemas legados (Bloco 1.4).
> Lê de fontes externas (Firebird/Fiorilli SIP por enquanto), transforma e
> carrega no schema do tenant ativo. **Mora em TENANT_APPS** — cada município
> tem seu próprio histórico de importações.

## Padrão de implementação

Pipeline ETL em 3 camadas (ADR-0009):

1. **adapters/** — leitura bruta da fonte (Firebird, CSV, etc.).
   Sem regra de negócio. Retorna `list[dict]`.
2. **services/mapping.py** — funções **puras** que transformam dict-SIP
   em dict-Arminda. Sem efeitos colaterais; **fácil de testar sem DB**.
3. **services/loaders/** — uma função por entidade que faz
   `Model.objects.update_or_create(...)` com a chave SIP estável.

## Idempotência

Todo loader usa `update_or_create(<chave_sip>, defaults={...})`. Re-rodar
o importador produz o mesmo estado final. Cada criação/atualização gera
um `SipImportRecord` para auditoria e detecção de drift na origem.

## Política de erros

Linha com problema NÃO interrompe o batch. É registrada como
`SipImportRecord(status="erro")`. Resumo final mostra contagem por
tipo de erro.

## Charset

`SIP.FDB` usa `WIN1252`. Sempre passar `charset="WIN1252"` ao conectar
via `firebirdsql.connect(...)`.

## Como rodar

```bash
# Sobe Firebird 2.5 com SIP.FDB attached
docker run -d --name fb25 -p 13050:3050 \
  -v /caminho/para/SIP.FDB:/firebird/data/SIP.FDB \
  -e ISC_PASSWORD=masterkey \
  jacobalberty/firebird:2.5-ss

# Cria usuário não-SYSDBA com nome do owner do FDB (FSCSIP no Fiorilli)
docker exec fb25 /usr/local/firebird/bin/gsec \
  -user sysdba -password masterkey -add FSCSIP -pw fscpw

# Roda o importador (dry-run primeiro)
python manage.py import_fiorilli_sip \
  --tenant mun_sao_raimundo \
  --host 127.0.0.1 --port 13050 \
  --database /firebird/data/SIP.FDB \
  --user FSCSIP --password fscpw \
  --tabelas cargos,lotacoes,servidores,dependentes \
  --dry-run
```

## Não fazer

- Não usar `bulk_create` em loaders críticos sem cobertura por testes —
  `update_or_create` é mais lento mas garante idempotência por linha.
- Não persistir credenciais do FDB no banco/config. Sempre passar via
  `--password` ou env `SIP_PASSWORD` no momento da execução.
- Não importar histórico financeiro (MOVIMENTO, EVENTOSFIXOS) nesta onda
  — depende do Bloco 2.
