"""
Testes da análise estática de dependências (Bloco 2.2).

Puros — sem DB. Cobrem:
- Extração de RUBRICA('X') das fórmulas
- Toposort com casos felizes
- Detecção de ciclo
- Detecção de dependência inexistente
"""

from __future__ import annotations

import pytest

from apps.calculo.dependencias import (
    DependenciaCiclicaError,
    DependenciaInexistenteError,
    RubricaParaOrdenar,
    extrair_dependencias,
    ordenar_topologicamente,
)


class TestExtrair:
    def test_sem_rubrica(self):
        assert extrair_dependencias("SALARIO_BASE * 0.10") == set()

    def test_formula_vazia(self):
        assert extrair_dependencias("") == set()

    def test_uma_rubrica_aspas_simples(self):
        assert extrair_dependencias("RUBRICA('SAL_BASE') * 0.10") == {"SAL_BASE"}

    def test_uma_rubrica_aspas_duplas(self):
        assert extrair_dependencias('RUBRICA("SAL_BASE") * 0.10') == {"SAL_BASE"}

    def test_multiplas_rubricas(self):
        formula = "RUBRICA('SAL_BASE') + RUBRICA('GRATIF') - RUBRICA('FALTAS')"
        assert extrair_dependencias(formula) == {"SAL_BASE", "GRATIF", "FALTAS"}

    def test_rubrica_aninhada_em_se(self):
        formula = "SE(RUBRICA('A') > 0, RUBRICA('B'), 0)"
        assert extrair_dependencias(formula) == {"A", "B"}

    def test_ignora_rubrica_com_argumento_dinamico(self):
        # RUBRICA(var) — análise estática não tem como saber o valor
        formula = "RUBRICA(codigo_var)"
        assert extrair_dependencias(formula) == set()


class TestOrdenar:
    def test_sem_dependencias(self):
        rubricas = [
            RubricaParaOrdenar("A", "1 + 1"),
            RubricaParaOrdenar("B", "2 * 2"),
        ]
        ordem = ordenar_topologicamente(rubricas)
        # Ordem alfabética entre rubricas independentes
        assert ordem == ["A", "B"]

    def test_dependencia_simples(self):
        rubricas = [
            RubricaParaOrdenar("INSS", "RUBRICA('SAL_BASE') * 0.11"),
            RubricaParaOrdenar("SAL_BASE", "SALARIO_BASE"),
        ]
        ordem = ordenar_topologicamente(rubricas)
        assert ordem == ["SAL_BASE", "INSS"]

    def test_cadeia_de_dependencias(self):
        # A → B → C: C primeiro, depois B, depois A
        rubricas = [
            RubricaParaOrdenar("A", "RUBRICA('B') + 1"),
            RubricaParaOrdenar("B", "RUBRICA('C') + 1"),
            RubricaParaOrdenar("C", "1"),
        ]
        assert ordenar_topologicamente(rubricas) == ["C", "B", "A"]

    def test_multiplas_dependencias(self):
        # FINAL depende de A, B, C; entre si A/B/C são independentes
        rubricas = [
            RubricaParaOrdenar("FINAL", "RUBRICA('A') + RUBRICA('B') + RUBRICA('C')"),
            RubricaParaOrdenar("A", "1"),
            RubricaParaOrdenar("B", "2"),
            RubricaParaOrdenar("C", "3"),
        ]
        ordem = ordenar_topologicamente(rubricas)
        assert ordem[:3] == ["A", "B", "C"]  # ordem alfabética entre livres
        assert ordem[-1] == "FINAL"

    def test_ciclo_simples_falha(self):
        rubricas = [
            RubricaParaOrdenar("A", "RUBRICA('B')"),
            RubricaParaOrdenar("B", "RUBRICA('A')"),
        ]
        with pytest.raises(DependenciaCiclicaError) as exc:
            ordenar_topologicamente(rubricas)
        assert exc.value.code == "DEPENDENCIA_CICLICA"

    def test_ciclo_longo_falha(self):
        # A → B → C → A
        rubricas = [
            RubricaParaOrdenar("A", "RUBRICA('B')"),
            RubricaParaOrdenar("B", "RUBRICA('C')"),
            RubricaParaOrdenar("C", "RUBRICA('A')"),
        ]
        with pytest.raises(DependenciaCiclicaError):
            ordenar_topologicamente(rubricas)

    def test_dependencia_inexistente_falha(self):
        rubricas = [
            RubricaParaOrdenar("A", "RUBRICA('FANTASMA')"),
        ]
        with pytest.raises(DependenciaInexistenteError) as exc:
            ordenar_topologicamente(rubricas)
        assert exc.value.code == "DEPENDENCIA_INEXISTENTE"
        assert "FANTASMA" in str(exc.value.args[0])

    def test_codigos_duplicados_falha(self):
        rubricas = [
            RubricaParaOrdenar("A", "1"),
            RubricaParaOrdenar("A", "2"),  # duplicado
        ]
        with pytest.raises(Exception, match="duplicados"):
            ordenar_topologicamente(rubricas)
