"""
Mappings puros entre dicts SIP e dicts Arminda (Bloco 1.4).

Funções aqui NÃO tocam o banco e NÃO importam models — só transformam.
Isso torna os testes triviais (input dict, output dict).

Cada mapping retorna `(chave_sip, defaults)` onde:
- `chave_sip` é o identificador estável usado em `update_or_create`.
- `defaults` é o kwargs do model Arminda.
"""

from __future__ import annotations

import hashlib
import json
import re
from datetime import date, datetime
from typing import Any

from apps.people.models import (
    EstadoCivil,
    NaturezaLotacao,
    NivelEscolaridade,
    Parentesco,
    Regime,
    Sexo,
)

# ============================================================
# Helpers
# ============================================================


def _bool_sip(v: Any) -> bool:
    """Fiorilli usa BOOLEAN_SIP = VARCHAR(1) com 'S'/'N'."""
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().upper() in ("S", "T", "1", "Y")
    return False


def _safe_str(v: Any, max_len: int | None = None) -> str:
    if v is None:
        return ""
    s = str(v).strip()
    if max_len:
        return s[:max_len]
    return s


def _safe_date(v: Any) -> date | None:
    if v is None:
        return None
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, str):
        try:
            return datetime.strptime(v.strip(), "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def payload_hash(payload: dict[str, Any]) -> str:
    """SHA-256 de um dict serializado de forma estável (chaves ordenadas)."""

    def default(obj: Any):
        if isinstance(obj, date | datetime):
            return obj.isoformat()
        return str(obj)

    serialized = json.dumps(payload, sort_keys=True, default=default, ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


# ============================================================
# Cargo
# ============================================================

# Mapeamento INSTRUCAO (SIP) → NivelEscolaridade (Arminda).
# SIP usa códigos eSocial (S2.5 da TabelaInstrucao):
#   01,02 → Fundamental incompleto/completo
#   03,04 → Médio incompleto/completo
#   05    → Superior incompleto
#   06    → Superior completo
#   07,08 → Pós (mestrado/doutorado)
_INSTRUCAO_SIP_TO_NIVEL = {
    "01": NivelEscolaridade.FUNDAMENTAL,
    "02": NivelEscolaridade.FUNDAMENTAL,
    "03": NivelEscolaridade.MEDIO,
    "04": NivelEscolaridade.MEDIO,
    "05": NivelEscolaridade.SUPERIOR,
    "06": NivelEscolaridade.SUPERIOR,
    "07": NivelEscolaridade.POS_GRADUACAO,
    "08": NivelEscolaridade.POS_GRADUACAO,
    "09": NivelEscolaridade.POS_GRADUACAO,
    "10": NivelEscolaridade.POS_GRADUACAO,
}


def map_cargo(row: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """
    Mapeia uma linha de CARGOS (SIP) → kwargs de `apps.people.Cargo`.

    Chave SIP estável: `{EMPRESA}-{CODIGO}` (sem espaços).
    Ex.: 001-PROFE
    """
    empresa = _safe_str(row.get("empresa"))
    codigo = _safe_str(row.get("codigo"))
    chave_sip = f"{empresa}-{codigo}"

    instrucao = _safe_str(row.get("instrucao"))
    nivel = _INSTRUCAO_SIP_TO_NIVEL.get(instrucao, NivelEscolaridade.MEDIO)

    vagas = (
        (row.get("vagacargo") or 0)
        + (row.get("vagafuncao") or 0)
        + (row.get("vagaemprego") or 0)
    )

    defaults = {
        "codigo": chave_sip[:20],
        "nome": _safe_str(row.get("nome"), max_len=200),
        "cbo": _safe_str(row.get("cbo"), max_len=10),
        "nivel_escolaridade": nivel,
        "data_criacao": _safe_date(row.get("dtcriacao")),
        "data_extincao": _safe_date(row.get("dtextincao")),
        "vagas_total": vagas if vagas > 0 else None,
        "dedicacao_exclusiva": _bool_sip(row.get("dedicacao_exclusiva")),
        "atribuicoes": _safe_str(row.get("atribuicoes")),
        "ativo": _safe_date(row.get("dtextincao")) is None,
    }
    return chave_sip, defaults


# ============================================================
# Lotação (LOCAL_TRABALHO)
# ============================================================


# Padrões de classificação da natureza da lotação, reusam a lógica das
# migrations 0004-0006 (mantida aqui pra que importações novas já classifiquem
# corretamente sem precisar de data migration adicional).
_PADROES_NATUREZA = {
    NaturezaLotacao.SAUDE: [
        r"\bsa[uú]de\b", r"\bacs\b", r"\bubs\b", r"\bhospital\b", r"\bsamu\b",
        r"\bvigil[âa]ncia\s+sanit[áa]ria\b", r"\bsesau\b", r"\bsemsa\b", r"\bsms\b",
        r"\benfermagem\b", r"\bm[eé]dico\b", r"\bsa[uú]de\s+da\s+fam[íi]lia\b",
        r"\bunidade\s+(de\s+)?sa[uú]de\b", r"\bcaps\b", r"\bpsf\b", r"\besf\b",
    ],
    NaturezaLotacao.EDUCACAO: [
        r"\beduca[çc][ãa]o\b", r"\bescola\b", r"\bcreche\b", r"\bemef\b", r"\bemei\b",
        r"\bbiblioteca\b", r"\bniiped\b", r"\bensino\b", r"\bsemed\b",
        r"\bunidade\s+escolar\b", r"\bsec(retaria)?\s+(municipal\s+)?de\s+edu[ck]",
        r"\bcentro\s+multidisciplinar.*pedag", r"^\s*esc\b", r"^\s*g\s+e\b",
        r"^\s*ge\b", r"\binfantil\b", r"\bcrescer\b",
    ],
    NaturezaLotacao.ASSISTENCIA: [
        r"\bassist[êe]ncia\s+social\b", r"\bcras\b", r"\bcreas\b",
        r"\bconselho\s+tutelar\b", r"\babrigo\b", r"\bbolsa\s+fam[íi]lia\b",
        r"\bcad[uú]nico\b", r"\bsemtas\b", r"\bsemas\b",
        r"\bdesenvolvimento\s+social\b", r"\bidoso\b",
        r"\bsec(retaria)?\s+(municipal\s+)?de\s+ass(ist)?", r"\bscfv\b",
        r"\bcrian[çc]a\s+feliz\b",
    ],
    NaturezaLotacao.ADMINISTRACAO: [
        r"\bgabinete\b", r"\bprefeit[oa]\b", r"\bvereador\b", r"\bc[âa]mara\b",
        r"\bfinan[çc]as?\b", r"\bfazenda\b", r"\btribut", r"\bcontroladoria\b",
        r"\bjur[íi]dico\b", r"\bprocuradoria\b", r"\brecursos\s+humanos\b",
        r"\bcentro\s+administrativo\b", r"\badmin", r"\bplanejamento\b",
        r"\borçamento\b", r"\bauditoria\b",
        r"\bsec(retaria)?\s+(municipal\s+)?de\s+admin",
        r"\bsec(retaria)?\s+(de\s+)?rela[çc][õo]es",
    ],
}


def _classifica_natureza(nome: str) -> str:
    """Retorna a natureza inferida do nome da lotação. 'outros' se não bater."""
    if not nome:
        return NaturezaLotacao.OUTROS
    n = nome.lower()
    for natureza, padroes in _PADROES_NATUREZA.items():
        for p in padroes:
            if re.search(p, n):
                return natureza
    return NaturezaLotacao.OUTROS


# Onda 1.4-bis: o código DEPDESPESA do Fiorilli usa primeiro dígito para
# indicar a função-governo (1=adm, 2=saúde, 3=educação, 4=assistência social,
# 5=administração II, 6=obras, 7=finanças). É uma convenção empírica do
# município-piloto — em outros municípios o esquema pode variar; nesse caso,
# o nome da unidade fala mais alto.
_PREFIXO_DEPDESPESA_NATUREZA = {
    "1": NaturezaLotacao.ADMINISTRACAO,
    "2": NaturezaLotacao.SAUDE,
    "3": NaturezaLotacao.EDUCACAO,
    "4": NaturezaLotacao.ASSISTENCIA,
    "5": NaturezaLotacao.ADMINISTRACAO,
    "6": NaturezaLotacao.OUTROS,  # obras — fica em "Outros" (não é 1 das 4 macro)
    "7": NaturezaLotacao.ADMINISTRACAO,  # finanças
}


def _classifica_natureza_unidade(codigo: str, nome: str) -> str:
    """
    Classifica a natureza de uma unidade orçamentária.

    Prefere o nome (mais específico) ao prefixo numérico (heurística).
    Só recorre ao prefixo quando o nome não casa com nenhum padrão claro.
    """
    por_nome = _classifica_natureza(nome)
    if por_nome != NaturezaLotacao.OUTROS:
        return por_nome
    if codigo and codigo[0] in _PREFIXO_DEPDESPESA_NATUREZA:
        return _PREFIXO_DEPDESPESA_NATUREZA[codigo[0]]
    return NaturezaLotacao.OUTROS


def map_unidade_orcamentaria(row: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """
    Mapeia uma linha de UNIDADE (SIP) → kwargs de `apps.people.UnidadeOrcamentaria`.

    Chave SIP estável: `{ANO}-{EMPRESA}-{DEPDESPESA}`.
    A natureza é inferida do nome (preferido) ou do prefixo numérico
    (fallback) via `_classifica_natureza_unidade`.
    """
    empresa = _safe_str(row.get("empresa"))
    codigo = _safe_str(row.get("depdespesa"))
    ano_raw = row.get("ano")
    try:
        ano = int(_safe_str(ano_raw))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"UNIDADE com ANO inválido: {ano_raw!r}") from exc
    nome = _safe_str(row.get("nome"), max_len=200)
    sigla = _safe_str(row.get("sigla"), max_len=20)

    chave_sip = f"{ano}-{empresa}-{codigo}"

    # CODIGO interno do Fiorilli (PK auto-increment da tabela UNIDADE) — é
    # POR ELE que TRABALHADOR.DEPDESPESA aponta. Sem isso, não tem como
    # cruzar vínculo → unidade orçamentária.
    codigo_interno_raw = row.get("codigo_interno")
    codigo_interno = None
    if codigo_interno_raw is not None:
        try:
            codigo_interno = int(codigo_interno_raw)
        except (TypeError, ValueError):
            codigo_interno = None

    return chave_sip, {
        "codigo": codigo,
        "codigo_interno_sip": codigo_interno,
        "ano": ano,
        "nome": nome,
        "sigla": sigla,
        "natureza": _classifica_natureza_unidade(codigo, nome),
        "ativo": True,
    }


def map_lotacao(row: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """
    Mapeia uma linha de LOCAL_TRABALHO (SIP) → kwargs de `apps.people.Lotacao`.

    Chave SIP estável: `{EMPRESA}-LT-{CODIGO}`.
    Não usamos hierarquia (lotacao_pai) na importação — fica plana.
    A natureza é inferida do nome via padrões; "outros" se nenhum bater.
    """
    empresa = _safe_str(row.get("empresa"))
    codigo = _safe_str(row.get("codigo"))
    chave_sip = f"{empresa}-LT-{codigo}"

    nome = _safe_str(row.get("nome"), max_len=200)
    # Sigla: pega as iniciais das palavras se nome tiver várias palavras
    palavras = nome.split()
    sigla = (
        "".join(p[0].upper() for p in palavras[:4])
        if len(palavras) >= 2
        else nome[:6].upper()
    )

    return chave_sip, {
        "codigo": chave_sip[:20],
        "nome": nome,
        "sigla": sigla[:20],
        "natureza": _classifica_natureza(nome),
        "lotacao_pai": None,
        "ativo": True,
    }


# ============================================================
# Servidor (PESSOA)
# ============================================================

_SEXO_SIP = {"M": Sexo.MASCULINO, "F": Sexo.FEMININO, "1": Sexo.MASCULINO, "2": Sexo.FEMININO}

_ESTADO_CIVIL_SIP = {
    "S": EstadoCivil.SOLTEIRO,
    "C": EstadoCivil.CASADO,
    "D": EstadoCivil.DIVORCIADO,
    "V": EstadoCivil.VIUVO,
    "U": EstadoCivil.UNIAO_ESTAVEL,
    # Códigos numéricos do eSocial:
    "1": EstadoCivil.SOLTEIRO,
    "2": EstadoCivil.CASADO,
    "3": EstadoCivil.DIVORCIADO,
    "4": EstadoCivil.VIUVO,
    "9": EstadoCivil.UNIAO_ESTAVEL,
}


def map_servidor(row: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """
    Mapeia uma linha de PESSOA (SIP) → kwargs de `apps.people.Servidor`.

    Chave SIP estável: o próprio CPF (já único em PESSOA).

    Servidor.matricula é a chave única do Arminda; o SIP não tem campo
    direto na PESSOA — usaremos o CPF como matrícula provisória se não
    houver vínculo associado. Quando o loader rodar com dados de
    TRABALHADOR, podemos sobrescrever com a matrícula real.
    """
    cpf = _safe_str(row.get("cpf"))
    if len(cpf) < 11:
        raise ValueError(f"CPF inválido em PESSOA: '{cpf}'")
    chave_sip = cpf

    sexo = _SEXO_SIP.get(_safe_str(row.get("sexo")).upper(), "")
    estado_civil = _ESTADO_CIVIL_SIP.get(_safe_str(row.get("estadocivil")).upper(), "")

    telefone = _safe_str(row.get("celular")) or _safe_str(row.get("telefone"))

    return chave_sip, {
        # Matrícula provisória; loader de Vínculo sobrescreve com REGISTRO real.
        "matricula": cpf,
        "nome": _safe_str(row.get("nome"), max_len=200),
        "cpf": cpf,
        "data_nascimento": _safe_date(row.get("dtnascimento")) or date(1970, 1, 1),
        "sexo": sexo,
        "estado_civil": estado_civil,
        "pis_pasep": _safe_str(row.get("pis"), max_len=20),
        "email": _safe_str(row.get("email"), max_len=254),
        "telefone": telefone[:20],
        "logradouro": _safe_str(row.get("endereco"), max_len=200),
        "numero": _safe_str(row.get("numero"), max_len=20),
        "complemento": _safe_str(row.get("compl"), max_len=100),
        "bairro": _safe_str(row.get("bairro"), max_len=100),
        "cidade": _safe_str(row.get("cidade"), max_len=100),
        "uf": _safe_str(row.get("uf"), max_len=2).upper(),
        "cep": _safe_str(row.get("cep"), max_len=10),
        # Enriquecidos (Bloco 1.4)
        "nacionalidade": _safe_str(row.get("nacionalidade"), max_len=2),
        "raca": _safe_str(row.get("raca"), max_len=1),
        "nome_pai": _safe_str(row.get("nomepai"), max_len=200),
        "nome_mae": _safe_str(row.get("nomemae"), max_len=200),
        "instrucao": _safe_str(row.get("instrucao"), max_len=2),
        "ativo": True,
    }


# ============================================================
# Vínculo (TRABALHADOR)
# ============================================================

# Mapeamento aproximado VINCULO.CODIGO (SIP) → Regime (Arminda).
# Os códigos exatos variam por município; este é o mapeamento padrão Fiorilli.
# VINCULO=01 (AGENTE POLITICO) cobre Prefeito, Vice e Vereadores — é
# regime ELETIVO no nosso modelo (não comissionado).
_VINCULO_SIP_TO_REGIME = {
    "01": Regime.ELETIVO,  # AGENTE_POLITICO (Prefeito, Vice, Vereadores)
    "02": Regime.COMISSIONADO,
    "03": Regime.ESTATUTARIO,
    "04": Regime.ESTATUTARIO,
    "05": Regime.CELETISTA,
    "06": Regime.TEMPORARIO,
    "07": Regime.ESTAGIARIO,
    "08": Regime.TEMPORARIO,
}


def map_vinculo(
    row: dict[str, Any],
    *,
    servidor_id: int,
    cargo_id: int,
    lotacao_id: int,
    unidade_orcamentaria_id: int | None = None,
) -> tuple[str, dict[str, Any]]:
    """
    Mapeia TRABALHADOR (SIP) → kwargs de `apps.people.VinculoFuncional`.

    Chave SIP estável: `{EMPRESA}-{REGISTRO}`.

    Recebe os IDs dos relacionamentos resolvidos (cargo, lotação, servidor)
    como parâmetros — o loader é responsável por resolver as FKs antes
    de chamar este mapping.
    """
    empresa = _safe_str(row.get("empresa"))
    registro = _safe_str(row.get("registro"))
    chave_sip = f"{empresa}-{registro}"

    regime_codigo = _safe_str(row.get("vinculo")).upper()
    regime = _VINCULO_SIP_TO_REGIME.get(regime_codigo, Regime.ESTATUTARIO)

    horas_semanais = row.get("horasemanal")
    if isinstance(horas_semanais, int | float) and 1 <= horas_semanais <= 60:
        carga = int(round(horas_semanais))
    else:
        carga = 40

    situacao = _safe_str(row.get("situacao")).upper()
    ativo = situacao not in ("D", "0", "9")  # D=demitido em Fiorilli

    return chave_sip, {
        "servidor_id": servidor_id,
        "cargo_id": cargo_id,
        "lotacao_id": lotacao_id,
        "unidade_orcamentaria_id": unidade_orcamentaria_id,
        "regime": regime,
        "data_admissao": _safe_date(row.get("dtadmissao")) or date(2020, 1, 1),
        "data_demissao": _safe_date(row.get("dtdemissao")),
        "carga_horaria": carga,
        "salario_base": 0,  # SIP guarda em outra tabela; preencher manualmente ou em onda futura
        "ativo": ativo,
        # Enriquecidos
        "matricula_contrato": registro[:20],
        "tipo_admissao": _safe_str(row.get("tipoadmissao"), max_len=2),
        "processo_admissao": _safe_str(row.get("processo"), max_len=20),
    }


# ============================================================
# Dependente
# ============================================================

_PARENTESCO_SIP = {
    "01": Parentesco.CONJUGE,
    "03": Parentesco.FILHO,
    "04": Parentesco.ENTEADO,
    "06": Parentesco.PAI_MAE,
}


def map_dependente(
    row: dict[str, Any], *, servidor_id: int
) -> tuple[str, dict[str, Any]]:
    """
    Mapeia DEPENDENTES (SIP) → kwargs de `apps.people.Dependente`.

    Chave SIP composta: `{CPF_TITULAR}-{NOME_NORMALIZADO}-{NASCIMENTO}`.
    """
    cpf_titular = _safe_str(row.get("cpf_titular"))
    if not cpf_titular:
        raise ValueError("Dependente sem CPF do titular (TRABALHADOR não encontrado).")

    nome = _safe_str(row.get("nome"), max_len=200)
    if not nome:
        raise ValueError("Dependente sem nome.")
    data_nasc = _safe_date(row.get("dtnascimento"))
    if not data_nasc:
        raise ValueError(f"Dependente '{nome}' sem data de nascimento.")

    nome_chave = "".join(c for c in nome.upper() if c.isalnum())[:30]
    chave_sip = f"{cpf_titular}-{nome_chave}-{data_nasc.isoformat()}"

    parentesco_codigo = _safe_str(row.get("parentesco"))
    parentesco = _PARENTESCO_SIP.get(parentesco_codigo, Parentesco.OUTRO)

    return chave_sip, {
        "servidor_id": servidor_id,
        "nome": nome,
        "cpf": _safe_str(row.get("cpf"), max_len=14),
        "data_nascimento": data_nasc,
        "parentesco": parentesco,
        "ir": _bool_sip(row.get("irrf")),
        "salario_familia": _bool_sip(row.get("salfamilia")),
    }
