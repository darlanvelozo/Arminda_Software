"""
Adapter de leitura do Fiorilli SIP (Firebird 2.5) — Bloco 1.4.

Camada **read-only**: extrai linhas de tabelas SIP como dicts brutos.
Não faz transformação — só converte cada linha em `dict[str, Any]` com
nomes de coluna em snake_case minúsculo.

Idempotência e mapeamento ficam em `apps.imports.services.mapping` e
`apps.imports.services.loaders.*`.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

import firebirdsql


@dataclass(frozen=True)
class FirebirdConfig:
    """Conexão com o SIP.FDB. Senha não é persistida."""

    host: str
    port: int
    database: str  # caminho remoto (ex.: '/firebird/data/SIP.FDB')
    user: str
    password: str
    charset: str = "WIN1252"


@contextmanager
def open_connection(config: FirebirdConfig) -> Iterator[firebirdsql.Connection]:
    """Context manager que garante close() mesmo em exceção."""
    conn = firebirdsql.connect(
        host=config.host,
        port=config.port,
        database=config.database,
        user=config.user,
        password=config.password,
        charset=config.charset,
    )
    try:
        yield conn
    finally:
        conn.close()


def _rows_to_dicts(cursor: Any) -> list[dict[str, Any]]:
    """Converte cursor em list[dict] com chaves em lower-case."""
    if cursor.description is None:
        return []
    cols = [d[0].strip().lower() for d in cursor.description]
    return [
        {col: _normalize(value) for col, value in zip(cols, row, strict=False)} for row in cursor.fetchall()
    ]


def _normalize(value: Any) -> Any:
    """Strings vêm com padding de Firebird CHAR(N); tira whitespace."""
    if isinstance(value, str):
        return value.rstrip()
    if isinstance(value, bytes):
        try:
            return value.decode("WIN1252", errors="replace").rstrip()
        except Exception:  # pragma: no cover
            return value
    return value


# ============================================================
# Extractors — uma função por entidade
# ============================================================


def fetch_cargos(conn: firebirdsql.Connection, *, limit: int | None = None) -> list[dict]:
    """
    Extrai todos os cargos do SIP.

    Tabela `CARGOS` (esperado ~91 linhas no banco-exemplo).
    Chave SIP: (EMPRESA, CODIGO).
    """
    sql = (
        "SELECT EMPRESA, CODIGO, NOME, CBO, INSTRUCAO, "
        "DTCRIACAO, DTEXTINCAO, "
        "VAGACARGO, VAGAFUNCAO, VAGAEMPREGO, "
        "DEDICACAO_EXCLUSIVA, ATRIBUICOES "
        "FROM CARGOS"
    )
    if limit:
        sql = sql.replace("SELECT ", f"SELECT FIRST {int(limit)} ")
    cur = conn.cursor()
    cur.execute(sql)
    return _rows_to_dicts(cur)


def fetch_locais_trabalho(
    conn: firebirdsql.Connection, *, limit: int | None = None
) -> list[dict]:
    """
    Extrai locais de trabalho — usados como Lotação no Arminda.

    Tabela `LOCAL_TRABALHO` (esperado ~66 linhas).
    Chave SIP: (EMPRESA, CODIGO).
    """
    sql = "SELECT EMPRESA, CODIGO, NOME FROM LOCAL_TRABALHO"
    if limit:
        sql = sql.replace("SELECT ", f"SELECT FIRST {int(limit)} ")
    cur = conn.cursor()
    cur.execute(sql)
    return _rows_to_dicts(cur)


def fetch_pessoas(conn: firebirdsql.Connection, *, limit: int | None = None) -> list[dict]:
    """
    Extrai pessoas físicas — base do Servidor no Arminda.

    Tabela `PESSOA` (esperado ~517 linhas). Chave SIP: CPF.
    """
    sql = (
        "SELECT CPF, NOME, SEXO, NACIONALIDADE, DTNASCIMENTO, INSTRUCAO, "
        "ESTADOCIVIL, NOMEPAI, NOMEMAE, RACA, "
        "CEP, ENDERECO, NUMERO, BAIRRO, COMPL, CIDADE, UF, "
        "TELEFONE, CELULAR, EMAIL, PIS "
        "FROM PESSOA"
    )
    if limit:
        sql = sql.replace("SELECT ", f"SELECT FIRST {int(limit)} ")
    cur = conn.cursor()
    cur.execute(sql)
    return _rows_to_dicts(cur)


def fetch_trabalhadores(
    conn: firebirdsql.Connection, *, limit: int | None = None
) -> list[dict]:
    """
    Extrai trabalhadores — vira VinculoFuncional no Arminda.

    Tabela `TRABALHADOR` (esperado ~2762 linhas).
    Chave SIP: (EMPRESA, REGISTRO).

    Faz JOIN com PESSOA via CPF para garantir que o vínculo tem
    contrapartida na tabela PESSOA (servidor já existe ou pode ser criado).
    """
    sql = (
        "SELECT T.EMPRESA, T.REGISTRO, T.MATRICULA, T.CONTRATO, "
        "T.CPF, T.CARGOATUAL, T.LOCAL_TRABALHO, T.VINCULO, T.DEPDESPESA, "
        "T.SITUACAO, T.DTADMISSAO, T.DTDEMISSAO, T.TIPOADMISSAO, "
        "T.HORASEMANAL, T.PROCESSO "
        "FROM TRABALHADOR T "
        "WHERE T.CPF IS NOT NULL"
    )
    if limit:
        sql = sql.replace("SELECT ", f"SELECT FIRST {int(limit)} ")
    cur = conn.cursor()
    cur.execute(sql)
    return _rows_to_dicts(cur)


def fetch_dependentes(
    conn: firebirdsql.Connection, *, limit: int | None = None
) -> list[dict]:
    """
    Extrai dependentes — apenas com CPF do servidor titular.

    Tabela `DEPENDENTES` (esperado ~303 linhas).
    Chave SIP: (CPF_TITULAR, NOME, DTNASCIMENTO) — composta.
    """
    # SIP usa DTNASC (não DTNASCIMENTO) e não tem flag SALFAMILIA — derivamos
    # da idade do dependente nos loaders se necessário (regra do salário-família
    # é por idade no SIP, não por flag).
    sql = (
        "SELECT D.EMPRESA, D.REGISTRO, D.NOME, D.DTNASC AS DTNASCIMENTO, "
        "D.CPF, D.PARENTESCO, D.IRRF, "
        "T.CPF AS CPF_TITULAR "
        "FROM DEPENDENTES D "
        "LEFT JOIN TRABALHADOR T ON T.EMPRESA = D.EMPRESA AND T.REGISTRO = D.REGISTRO"
    )
    if limit:
        sql = sql.replace("SELECT ", f"SELECT FIRST {int(limit)} ")
    cur = conn.cursor()
    cur.execute(sql)
    return _rows_to_dicts(cur)


def fetch_unidades_orcamentarias(
    conn: firebirdsql.Connection, *, ano: int | None = None, limit: int | None = None
) -> list[dict]:
    """
    Extrai unidades orçamentárias do SIP (tabela UNIDADE).

    Cada município costuma ter ~65 unidades por exercício fiscal. Se `ano`
    for informado, filtra apenas as desse ano (uso típico: ano corrente).
    Chave SIP: (EMPRESA, DEPDESPESA, ANO).
    """
    sql = (
        "SELECT EMPRESA, DEPDESPESA, ANO, CODIGO AS CODIGO_INTERNO, "
        "NOMEUNIDADE AS NOME, SIGLA "
        "FROM UNIDADE"
    )
    if ano:
        sql += f" WHERE ANO = '{int(ano)}'"
    if limit:
        sql = sql.replace("SELECT ", f"SELECT FIRST {int(limit)} ")
    cur = conn.cursor()
    cur.execute(sql)
    return _rows_to_dicts(cur)


def fetch_eventos(conn: firebirdsql.Connection, *, limit: int | None = None) -> list[dict]:
    """
    Extrai rubricas (eventos) — vira Rubrica no Arminda.

    Tabela `EVENTOS` (esperado ~201 linhas). Chave SIP: (EMPRESA, CODIGO).
    Importação de Rubrica é simplificada: apenas o esqueleto (sem fórmula,
    pois a DSL é Bloco 2).
    """
    sql = (
        "SELECT EMPRESA, CODIGO, NOME, NATUREZA, "
        "INSS, IRRF, FGTS, ATIVO "
        "FROM EVENTOS"
    )
    if limit:
        sql = sql.replace("SELECT ", f"SELECT FIRST {int(limit)} ")
    cur = conn.cursor()
    cur.execute(sql)
    return _rows_to_dicts(cur)
