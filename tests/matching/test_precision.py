# -*- coding: utf-8 -*-
"""
Test de Precisión de Matching ESCO
===================================

Valida la precisión del matching ESCO usando el gold set manual.

Ejecución:
    pytest tests/matching/test_precision.py -v
    pytest tests/matching/test_precision.py -v --tb=short
"""

import pytest
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Import fixtures desde conftest
from tests.conftest import parse_score


class TestMatchingPrecision:
    """Tests de precisión del matching ESCO."""

    MINIMUM_PRECISION = 0.80  # 80% mínimo requerido

    def test_gold_set_exists(self, matching_gold_set):
        """Verifica que el gold set existe y tiene casos."""
        assert len(matching_gold_set) > 0, "Gold set está vacío"
        assert len(matching_gold_set) >= 10, f"Gold set muy pequeño: {len(matching_gold_set)} casos"

    def test_gold_set_structure(self, matching_gold_set):
        """Verifica estructura del gold set."""
        for case in matching_gold_set:
            assert 'id_oferta' in case, f"Caso sin id_oferta: {case}"
            assert 'esco_ok' in case, f"Caso sin esco_ok: {case}"

    def test_matching_precision(self, db_cursor, matching_gold_set, score_parser):
        """
        Test principal: valida precisión contra gold set.

        Precisión = casos correctos / total casos
        Objetivo: >= 80%
        """
        # Obtener IDs del gold set
        gold_ids = [str(case['id_oferta']) for case in matching_gold_set]
        gold_lookup = {str(c['id_oferta']): c for c in matching_gold_set}

        # Query matching results
        placeholders = ','.join(['?'] * len(gold_ids))
        db_cursor.execute(f'''
            SELECT
                m.id_oferta,
                o.titulo,
                m.esco_occupation_label,
                m.score_final_ponderado,
                m.isco_code,
                m.matching_version
            FROM ofertas_esco_matching m
            JOIN ofertas o ON CAST(m.id_oferta AS TEXT) = CAST(o.id_oferta AS TEXT)
            WHERE m.id_oferta IN ({placeholders})
        ''', gold_ids)

        db_results = {}
        for row in db_cursor.fetchall():
            db_results[str(row[0])] = {
                'titulo': row[1],
                'esco_label': row[2],
                'score': score_parser(row[3]),
                'isco_code': row[4],
                'version': row[5]
            }

        # Calcular precisión
        correct = 0
        incorrect = 0
        pending = 0
        errors_by_type = {}
        details = []

        for id_oferta in gold_ids:
            gold_case = gold_lookup[id_oferta]
            expected_ok = gold_case.get('esco_ok', True)

            if id_oferta in db_results:
                result = db_results[id_oferta]
                has_match = result['esco_label'] is not None

                if has_match:
                    if expected_ok:
                        # Caso marcado como correcto, tiene match
                        correct += 1
                        status = 'PASS'
                    else:
                        # Caso marcado como error conocido
                        incorrect += 1
                        status = 'KNOWN_ERROR'
                        error_type = gold_case.get('tipo_error', 'unknown')
                        errors_by_type[error_type] = errors_by_type.get(error_type, 0) + 1
                else:
                    pending += 1
                    status = 'PENDING'

                details.append({
                    'id_oferta': id_oferta,
                    'titulo': result['titulo'][:40] if result['titulo'] else 'N/A',
                    'esco_label': result['esco_label'][:40] if result['esco_label'] else 'PENDING',
                    'score': result['score'],
                    'expected_ok': expected_ok,
                    'status': status
                })
            else:
                pending += 1
                details.append({
                    'id_oferta': id_oferta,
                    'status': 'NO_DATA'
                })

        # Calcular métricas
        total = len(matching_gold_set)
        precision = correct / total if total > 0 else 0

        # Reportar resultados
        print("\n" + "=" * 70)
        print("RESULTADO TEST DE PRECISIÓN")
        print("=" * 70)
        print(f"Total casos gold set:  {total}")
        print(f"Correctos:             {correct}")
        print(f"Errores conocidos:     {incorrect}")
        print(f"Pendientes:            {pending}")
        print(f"PRECISIÓN:             {precision*100:.1f}%")
        print(f"Objetivo mínimo:       {self.MINIMUM_PRECISION*100:.0f}%")
        print("=" * 70)

        if errors_by_type:
            print("\nErrores por tipo:")
            for error_type, count in sorted(errors_by_type.items(), key=lambda x: -x[1]):
                print(f"  - {error_type}: {count}")

        # Guardar resultados para historial
        self._save_results(precision, total, correct, incorrect, pending, errors_by_type)

        # Assert final
        assert precision >= self.MINIMUM_PRECISION, \
            f"Precisión {precision*100:.1f}% menor a objetivo {self.MINIMUM_PRECISION*100:.0f}%"

    def _save_results(self, precision, total, correct, incorrect, pending, errors_by_type):
        """Guarda resultados en historial (opcional)."""
        metrics_path = Path(__file__).parent.parent.parent / "metrics"
        metrics_path.mkdir(exist_ok=True)
        history_file = metrics_path / "gold_set_history.json"

        # Cargar historial existente
        history = []
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                history = []

        # Agregar nuevo resultado
        result = {
            'timestamp': datetime.now().isoformat(),
            'precision': round(precision * 100, 1),
            'total': total,
            'correct': correct,
            'incorrect': incorrect,
            'pending': pending,
            'errors_by_type': errors_by_type
        }
        history.append(result)

        # Guardar (mantener últimos 100)
        history = history[-100:]
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)


class TestMatchingCoverage:
    """Tests de cobertura del matching."""

    def test_all_gold_set_ids_have_matching(self, db_cursor, matching_gold_set):
        """Verifica que todos los IDs del gold set tienen resultado de matching."""
        gold_ids = [str(case['id_oferta']) for case in matching_gold_set]
        placeholders = ','.join(['?'] * len(gold_ids))

        db_cursor.execute(f'''
            SELECT id_oferta FROM ofertas_esco_matching
            WHERE id_oferta IN ({placeholders})
        ''', gold_ids)

        matched_ids = {str(row[0]) for row in db_cursor.fetchall()}
        missing = set(gold_ids) - matched_ids

        coverage = len(matched_ids) / len(gold_ids) * 100

        print(f"\nCobertura matching: {len(matched_ids)}/{len(gold_ids)} ({coverage:.1f}%)")

        if missing:
            print(f"IDs sin matching: {list(missing)[:10]}...")

        assert coverage >= 90, f"Cobertura muy baja: {coverage:.1f}%"


class TestMatchingVersion:
    """Tests de versión del matching."""

    def test_matching_version_consistency(self, db_cursor, matching_gold_set):
        """Verifica que todos los matches usan la misma versión."""
        gold_ids = [str(case['id_oferta']) for case in matching_gold_set]
        placeholders = ','.join(['?'] * len(gold_ids))

        db_cursor.execute(f'''
            SELECT DISTINCT matching_version FROM ofertas_esco_matching
            WHERE id_oferta IN ({placeholders})
        ''', gold_ids)

        versions = [row[0] for row in db_cursor.fetchall()]

        print(f"\nVersiones encontradas: {versions}")

        # Advertencia si hay múltiples versiones
        if len(versions) > 1:
            print("ADVERTENCIA: Múltiples versiones de matching en gold set")


# ============================================================================
# Runner para ejecución directa
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
