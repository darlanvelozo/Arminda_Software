"""
Popula o tenant smoke_arminda com dataset realista para demonstração:
- 7 lotações (secretarias)
- 5 unidades orçamentárias (2026)
- 10 cargos
- ~25 servidores variados (regimes, idades, salários, dependentes)
- 11 rubricas com fórmulas DSL
- 3 folhas mensais calculadas (mar/abr/mai 2026)
"""
from __future__ import annotations

import random
from datetime import date
from decimal import Decimal

from django.db import connection, transaction
from django_tenants.utils import schema_context

from apps.core.models import Municipio
from apps.payroll.models import Folha, Rubrica, StatusFolha, TipoFolha, TipoRubrica
from apps.payroll.services.calculo import calcular_folha
from apps.people.models import (
    Cargo,
    Dependente,
    Lotacao,
    NaturezaLotacao,
    NivelEscolaridade,
    Parentesco,
    Regime,
    Servidor,
    Sexo,
    UnidadeOrcamentaria,
    VinculoFuncional,
)

random.seed(42)


def gen_cpf() -> str:
    """Gera CPF válido (com checksum correto)."""
    while True:
        n = [random.randint(0, 9) for _ in range(9)]
        # 1º dígito
        s = sum((10 - i) * d for i, d in enumerate(n))
        d1 = (s * 10) % 11
        if d1 == 10:
            d1 = 0
        n.append(d1)
        # 2º dígito
        s = sum((11 - i) * d for i, d in enumerate(n))
        d2 = (s * 10) % 11
        if d2 == 10:
            d2 = 0
        n.append(d2)
        cpf = "".join(str(x) for x in n)
        # rejeita CPFs com todos dígitos iguais (inválidos)
        if len(set(cpf)) > 1:
            return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


SCHEMA = "smoke_arminda"


def main():
    Municipio.objects.get(schema_name=SCHEMA)
    with schema_context(SCHEMA):
        with transaction.atomic():
            limpa_seed_anterior()
            seed_estruturas()
            seed_servidores()
            seed_rubricas()
            calcula_folhas()


def limpa_seed_anterior():
    """Remove lançamentos+folhas antigas do smoke E2E para liberar deletes."""
    print("→ Limpeza prévia")
    from apps.payroll.models import Lancamento
    Lancamento.objects.all().delete()
    Folha.objects.all().delete()


def seed_estruturas():
    print("→ Lotações")
    lotacoes_data = [
        ("SEMED", "Secretaria Municipal de Educação", "SEMED", NaturezaLotacao.EDUCACAO),
        ("SEMSA", "Secretaria Municipal de Saúde", "SEMSA", NaturezaLotacao.SAUDE),
        ("SMAS", "Secretaria de Assistência Social", "SMAS", NaturezaLotacao.ASSISTENCIA),
        ("SEMAD", "Secretaria de Administração", "SEMAD", NaturezaLotacao.ADMINISTRACAO),
        ("GAB", "Gabinete do Prefeito", "GAB", NaturezaLotacao.ADMINISTRACAO),
        ("CMSMOKE", "Câmara Municipal", "CM", NaturezaLotacao.ADMINISTRACAO),
        ("FMS", "Fundo Municipal de Saúde", "FMS", NaturezaLotacao.SAUDE),
    ]
    for codigo, nome, sigla, natureza in lotacoes_data:
        Lotacao.objects.update_or_create(
            codigo=codigo,
            defaults={"nome": nome, "sigla": sigla, "natureza": natureza},
        )

    print("→ Unidades orçamentárias 2026")
    uos = [
        ("100001", "Prefeitura — Adm Central", "PREF-ADM", NaturezaLotacao.ADMINISTRACAO, 1001),
        ("200001", "Secretaria de Educação", "SEMED", NaturezaLotacao.EDUCACAO, 2001),
        ("200002", "Fundo Municipal de Saúde", "FMS", NaturezaLotacao.SAUDE, 2002),
        ("200003", "FMAS — Assistência", "FMAS", NaturezaLotacao.ASSISTENCIA, 2003),
        ("300001", "Câmara Municipal", "CM", NaturezaLotacao.ADMINISTRACAO, 3001),
    ]
    for codigo, nome, sigla, nat, sip in uos:
        UnidadeOrcamentaria.objects.update_or_create(
            codigo=codigo,
            ano=2026,
            defaults={
                "nome": nome,
                "sigla": sigla,
                "natureza": nat,
                "codigo_interno_sip": sip,
            },
        )

    print("→ Cargos")
    cargos_data = [
        ("PROF1", "Professor I — Ensino Fundamental", "2312-05", NivelEscolaridade.SUPERIOR),
        ("PROF2", "Professor II — Ensino Médio", "2321-05", NivelEscolaridade.SUPERIOR),
        ("DIRESC", "Diretor Escolar", "1314-15", NivelEscolaridade.SUPERIOR),
        ("ENF", "Enfermeiro", "2235-05", NivelEscolaridade.SUPERIOR),
        ("ACS", "Agente Comunitário de Saúde", "5151-10", NivelEscolaridade.MEDIO),
        ("MED", "Médico Clínico Geral", "2251-25", NivelEscolaridade.SUPERIOR),
        ("ASOC", "Assistente Social", "2516-05", NivelEscolaridade.SUPERIOR),
        ("AUX", "Auxiliar Administrativo", "4110-05", NivelEscolaridade.MEDIO),
        ("MOTO", "Motorista", "7823-05", NivelEscolaridade.FUNDAMENTAL),
        ("SECMUN", "Secretário Municipal", "1141-15", NivelEscolaridade.SUPERIOR),
        ("VEREA", "Vereador", "1141-10", NivelEscolaridade.MEDIO),
    ]
    for codigo, nome, cbo, esc in cargos_data:
        Cargo.objects.update_or_create(
            codigo=codigo,
            defaults={"nome": nome, "cbo": cbo, "nivel_escolaridade": esc},
        )


# Dataset de servidores. Cada tupla:
# (matricula, nome, sexo, ano_nasc, mes_nasc, dia_nasc,
#  cargo_codigo, lotacao_codigo, uo_codigo, regime, salario, ano_adm, mes_adm, n_dep_ir, n_dep_salfam)
SERVIDORES = [
    ("E001", "Maria Aparecida da Silva", Sexo.FEMININO, 1985, 4, 12, "PROF1", "SEMED", "200001", Regime.ESTATUTARIO, "3500.00", 2014, 2, 2, 1),
    ("E002", "João Pedro Santos", Sexo.MASCULINO, 1978, 9, 30, "DIRESC", "SEMED", "200001", Regime.ESTATUTARIO, "5800.00", 2008, 6, 1, 0),
    ("E003", "Ana Lúcia Ferreira", Sexo.FEMININO, 1990, 1, 22, "PROF2", "SEMED", "200001", Regime.ESTATUTARIO, "4200.00", 2017, 3, 0, 0),
    ("E004", "Carlos Eduardo Lima", Sexo.MASCULINO, 1972, 7, 5, "PROF1", "SEMED", "200001", Regime.ESTATUTARIO, "4100.00", 2001, 8, 3, 2),
    ("E005", "Beatriz Oliveira", Sexo.FEMININO, 1995, 11, 18, "ACS", "SEMSA", "200002", Regime.ESTATUTARIO, "1800.00", 2020, 1, 0, 0),
    ("E006", "Roberto Almeida Junior", Sexo.MASCULINO, 1965, 3, 14, "MED", "FMS", "200002", Regime.ESTATUTARIO, "12500.00", 1995, 5, 2, 0),
    ("E007", "Luciana Costa Pinheiro", Sexo.FEMININO, 1982, 5, 27, "ENF", "FMS", "200002", Regime.ESTATUTARIO, "5500.00", 2010, 11, 1, 1),
    ("E008", "Marcos Vinícius Silva", Sexo.MASCULINO, 1988, 12, 3, "ENF", "SEMSA", "200002", Regime.ESTATUTARIO, "5200.00", 2015, 7, 0, 0),
    ("E009", "Patrícia Mendes", Sexo.FEMININO, 1980, 8, 19, "ASOC", "SMAS", "200003", Regime.ESTATUTARIO, "4800.00", 2009, 4, 2, 1),
    ("E010", "Fernanda Rocha", Sexo.FEMININO, 1992, 6, 7, "ASOC", "SMAS", "200003", Regime.ESTATUTARIO, "4500.00", 2018, 9, 1, 0),
    ("E011", "Antônio Carlos Pereira", Sexo.MASCULINO, 1970, 2, 11, "AUX", "SEMAD", "100001", Regime.ESTATUTARIO, "2400.00", 1998, 3, 1, 0),
    ("E012", "Mariana Souza", Sexo.FEMININO, 1996, 10, 15, "AUX", "SEMAD", "100001", Regime.ESTATUTARIO, "2200.00", 2021, 2, 0, 0),
    ("E013", "Paulo Henrique Dias", Sexo.MASCULINO, 1975, 4, 22, "MOTO", "SEMSA", "200002", Regime.ESTATUTARIO, "2600.00", 2005, 10, 2, 1),
    ("E014", "Cláudia Regina Barbosa", Sexo.FEMININO, 1968, 11, 8, "PROF2", "SEMED", "200001", Regime.ESTATUTARIO, "5100.00", 1992, 2, 0, 0),
    ("E015", "Diego Martins Lopes", Sexo.MASCULINO, 1991, 7, 25, "ACS", "SEMSA", "200002", Regime.ESTATUTARIO, "1750.00", 2019, 6, 1, 1),
    ("C001", "Joana D'Arc Vieira", Sexo.FEMININO, 1973, 5, 9, "SECMUN", "GAB", "100001", Regime.COMISSIONADO, "9500.00", 2021, 1, 0, 0),
    ("C002", "Rafael Toledo", Sexo.MASCULINO, 1968, 1, 17, "SECMUN", "SEMSA", "200002", Regime.COMISSIONADO, "9500.00", 2021, 1, 1, 0),
    ("C003", "Helena Maciel", Sexo.FEMININO, 1980, 9, 4, "SECMUN", "SEMED", "200001", Regime.COMISSIONADO, "9500.00", 2021, 1, 2, 0),
    ("T001", "Pedro Alves Ribeiro", Sexo.MASCULINO, 1998, 12, 12, "AUX", "SEMAD", "100001", Regime.TEMPORARIO, "2000.00", 2024, 8, 0, 0),
    ("T002", "Larissa Câmara", Sexo.FEMININO, 1999, 3, 28, "AUX", "SMAS", "200003", Regime.TEMPORARIO, "2000.00", 2024, 9, 0, 0),
    ("V001", "Sebastião Marques", Sexo.MASCULINO, 1958, 6, 20, "VEREA", "CMSMOKE", "300001", Regime.ELETIVO, "8500.00", 2021, 1, 0, 0),
    ("V002", "Glória Santos", Sexo.FEMININO, 1962, 4, 11, "VEREA", "CMSMOKE", "300001", Regime.ELETIVO, "8500.00", 2021, 1, 1, 0),
    ("V003", "Edmilson Tavares", Sexo.MASCULINO, 1969, 8, 16, "VEREA", "CMSMOKE", "300001", Regime.ELETIVO, "8500.00", 2021, 1, 0, 0),
]


def seed_servidores():
    print(f"→ Servidores ({len(SERVIDORES)} total)")
    cargos = {c.codigo: c for c in Cargo.objects.all()}
    lotacoes = {l.codigo: l for l in Lotacao.objects.all()}
    uos = {u.codigo: u for u in UnidadeOrcamentaria.objects.filter(ano=2026)}

    for tup in SERVIDORES:
        (
            matricula,
            nome,
            sexo,
            ano_n,
            mes_n,
            dia_n,
            cargo_codigo,
            lotacao_codigo,
            uo_codigo,
            regime,
            salario,
            ano_adm,
            mes_adm,
            n_dep_ir,
            n_dep_salfam,
        ) = tup

        servidor, criado_s = Servidor.objects.get_or_create(
            matricula=matricula,
            defaults={
                "nome": nome,
                "cpf": gen_cpf(),
                "data_nascimento": date(ano_n, mes_n, dia_n),
                "sexo": sexo,
            },
        )

        VinculoFuncional.objects.update_or_create(
            servidor=servidor,
            cargo=cargos[cargo_codigo],
            defaults={
                "lotacao": lotacoes[lotacao_codigo],
                "unidade_orcamentaria": uos.get(uo_codigo),
                "regime": regime,
                "data_admissao": date(ano_adm, mes_adm, 1),
                "carga_horaria": 40,
                "salario_base": Decimal(salario),
                "ativo": True,
            },
        )

        # Limpa dependentes antigos e recria
        Dependente.objects.filter(servidor=servidor).delete()
        for i in range(n_dep_ir):
            ano_filho = ano_n + random.randint(22, 35)
            Dependente.objects.create(
                servidor=servidor,
                nome=f"Dependente IR {i + 1} de {nome.split()[0]}",
                data_nascimento=date(min(ano_filho, 2024), random.randint(1, 12), random.randint(1, 28)),
                parentesco=Parentesco.FILHO,
                ir=True,
                salario_familia=False,
            )
        for i in range(n_dep_salfam):
            ano_filho = ano_n + random.randint(28, 40)
            Dependente.objects.create(
                servidor=servidor,
                nome=f"Dependente Sal-Fam {i + 1} de {nome.split()[0]}",
                data_nascimento=date(min(ano_filho, 2024), random.randint(1, 12), random.randint(1, 28)),
                parentesco=Parentesco.FILHO,
                ir=False,
                salario_familia=True,
            )


RUBRICAS = [
    ("SAL_BASE", "Salário-base", TipoRubrica.PROVENTO, "SALARIO_BASE", True, True, True),
    ("ADIC_TS", "Adicional por tempo de serviço (1%/ano)", TipoRubrica.PROVENTO, "SALARIO_BASE * 0.01 * TEMPO_SERVICO_ANOS", True, True, True),
    ("SAL_FAM", "Salário-família", TipoRubrica.PROVENTO, "DEPENDENTES_SALFAM * 65", False, False, False),
    ("GRATIF", "Gratificação por nível", TipoRubrica.PROVENTO, "SE(SALARIO_BASE > 4000, 250, 100)", True, True, True),
    ("INSS", "INSS 11% (provisório)", TipoRubrica.DESCONTO, "RUBRICA('SAL_BASE') * 0.11", False, False, False),
    ("IRRF", "IRRF simplificado (provisório)", TipoRubrica.DESCONTO, "ARRED(MAX(RUBRICA('SAL_BASE') * 0.075 - DEPENDENTES * 189.59 - 158, 0), 2)", False, False, False),
    ("PSAUDE", "Plano de saúde", TipoRubrica.DESCONTO, "120", False, False, False),
    ("VT", "Vale-transporte (6%, teto 200)", TipoRubrica.DESCONTO, "MIN(SALARIO_BASE * 0.06, 200)", False, False, False),
    ("FALTAS_D", "Desconto por faltas", TipoRubrica.DESCONTO, "SALARIO_BASE / 30 * FALTAS", False, False, False),
    ("BASE_INSS", "Base INSS (informativa)", TipoRubrica.INFORMATIVA, "RUBRICA('SAL_BASE') + RUBRICA('ADIC_TS') + RUBRICA('GRATIF')", False, False, False),
    ("BASE_FGTS", "Base FGTS (informativa)", TipoRubrica.INFORMATIVA, "RUBRICA('SAL_BASE') + RUBRICA('ADIC_TS')", False, False, False),
]


def seed_rubricas():
    print(f"→ Rubricas ({len(RUBRICAS)} total)")
    # Remove rubricas antigas do smoke (SAL/INSS criadas no smoke E2E) que conflitam
    Rubrica.objects.filter(codigo__in=["SAL"]).delete()

    for codigo, nome, tipo, formula, incide_inss, incide_irrf, incide_fgts in RUBRICAS:
        Rubrica.objects.update_or_create(
            codigo=codigo,
            defaults={
                "nome": nome,
                "tipo": tipo,
                "formula": formula,
                "incide_inss": incide_inss,
                "incide_irrf": incide_irrf,
                "incide_fgts": incide_fgts,
                "ativo": True,
            },
        )


COMPETENCIAS = [
    date(2026, 3, 1),
    date(2026, 4, 1),
    date(2026, 5, 1),
]


def calcula_folhas():
    print(f"→ Folhas ({len(COMPETENCIAS)} competências)")
    for comp in COMPETENCIAS:
        folha, criada = Folha.objects.get_or_create(
            competencia=comp,
            tipo=TipoFolha.MENSAL,
            defaults={"status": StatusFolha.ABERTA},
        )
        rel = calcular_folha(folha)
        print(
            f"  {comp.strftime('%m/%Y')}: "
            f"{rel.vinculos_processados} vínculos × {rel.rubricas_processadas} rubricas → "
            f"{rel.lancamentos_criados} novos / {rel.lancamentos_atualizados} atualizados / "
            f"{rel.lancamentos_removidos} removidos, {len(rel.erros)} erros"
        )


if __name__ == "__main__":
    main()
    print("\n✅ Tenant smoke_arminda populado.")
