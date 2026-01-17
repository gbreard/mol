"""
Auto-corrector del pipeline MOL.
Aplica correcciones automaticas y escala a Claude cuando necesario.

Version: 1.0
Fecha: 2026-01-14

Uso:
    from database.auto_corrector import AutoCorrector

    corrector = AutoCorrector(db_conn)
    resultado = corrector.procesar_errores(errores_validacion)
"""

import json
import sqlite3
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict


class AutoCorrector:
    """Corrector automatico basado en auto_correction_map.json."""

    def __init__(self, db_conn: Optional[sqlite3.Connection] = None, config_dir: Optional[Path] = None):
        """
        Inicializa el corrector.

        Args:
            db_conn: Conexion a la base de datos SQLite
            config_dir: Directorio de configs. Default: config/
        """
        self.config_dir = config_dir or Path(__file__).parent.parent / "config"
        self.db_conn = db_conn

        # Cargar configs
        self.correction_map = self._load_json("auto_correction_map.json")
        self.diagnostic_patterns = self._load_json("diagnostic_patterns.json")

        # Cola de errores para Claude
        self.cola_claude = defaultdict(list)

        # Historial de correcciones
        self.correcciones_aplicadas = []

    def _load_json(self, filename: str) -> Dict:
        """Carga un archivo JSON de config."""
        path = self.config_dir / filename
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def procesar_errores(self, resultados_validacion: Dict) -> Dict[str, Any]:
        """
        Procesa errores de validacion y aplica correcciones.

        Args:
            resultados_validacion: Output de AutoValidator.validar_lote()

        Returns:
            Diccionario con:
            - auto_corregidos: Ofertas corregidas automaticamente
            - escalados_claude: Ofertas que requieren analisis de Claude
            - sin_accion: Ofertas sin accion disponible
            - correcciones_detalle: Detalle de cada correccion
        """
        resultado = {
            "auto_corregidos": [],
            "escalados_claude": [],
            "sin_accion": [],
            "correcciones_detalle": [],
            "timestamp": datetime.now().isoformat()
        }

        errores_detalle = resultados_validacion.get("errores_detalle", [])

        for item in errores_detalle:
            id_oferta = item["id_oferta"]

            for error in item["errores"]:
                diagnostico = error.get("diagnostico")
                correccion_config = self.correction_map.get("correcciones", {}).get(diagnostico)

                if not correccion_config:
                    resultado["sin_accion"].append({
                        "id_oferta": id_oferta,
                        "diagnostico": diagnostico,
                        "motivo": "No hay config de correccion definido"
                    })
                    continue

                tipo_accion = correccion_config.get("tipo_accion")

                if tipo_accion == "auto_corregir":
                    # Aplicar correccion automatica
                    exito = self._aplicar_auto_correccion(id_oferta, error, correccion_config)
                    if exito:
                        resultado["auto_corregidos"].append(id_oferta)
                        resultado["correcciones_detalle"].append({
                            "id_oferta": id_oferta,
                            "tipo": "auto_corregido",
                            "diagnostico": diagnostico,
                            "accion": correccion_config.get("descripcion")
                        })
                    else:
                        resultado["sin_accion"].append({
                            "id_oferta": id_oferta,
                            "diagnostico": diagnostico,
                            "motivo": "Error al aplicar auto-correccion"
                        })

                elif tipo_accion == "aplicar_config":
                    # Buscar config existente o escalar
                    config_existe = self._buscar_config_existente(error, correccion_config)
                    if config_existe:
                        # Marcar para reprocesamiento
                        resultado["correcciones_detalle"].append({
                            "id_oferta": id_oferta,
                            "tipo": "reprocesar",
                            "diagnostico": diagnostico,
                            "config": correccion_config.get("config"),
                            "accion": "Reprocesar con config existente"
                        })
                    else:
                        # Escalar a Claude
                        self._agregar_a_cola_claude(id_oferta, error, correccion_config)
                        resultado["escalados_claude"].append(id_oferta)

                elif tipo_accion == "escalar_claude":
                    # Siempre escalar a Claude
                    self._agregar_a_cola_claude(id_oferta, error, correccion_config)
                    resultado["escalados_claude"].append(id_oferta)

        # Agrupar errores para Claude
        resultado["patrones_para_claude"] = self._generar_patrones_claude()

        return resultado

    def _aplicar_auto_correccion(self, id_oferta: str, error: Dict, config: Dict) -> bool:
        """
        Aplica una correccion automatica a la BD.

        Args:
            id_oferta: ID de la oferta
            error: Error detectado
            config: Config de correccion

        Returns:
            True si se aplico correctamente
        """
        if not self.db_conn:
            return False

        ejecutar = config.get("ejecutar", {})
        funcion = ejecutar.get("funcion")

        try:
            if funcion == "set_campo":
                campo = ejecutar.get("campo")
                valor_template = ejecutar.get("valor_template", ejecutar.get("valor"))

                # Expandir template si es necesario
                if "{" in str(valor_template):
                    # Obtener datos de la oferta para expandir template
                    cursor = self.db_conn.execute(
                        "SELECT localidad FROM ofertas_nlp WHERE id_oferta = ?",
                        (id_oferta,)
                    )
                    row = cursor.fetchone()
                    if row:
                        localidad = row[0] or ""
                        # Detectar pais
                        paises = {
                            "Paraguay": "Paraguay",
                            "Asuncion": "Paraguay",
                            "Asunción": "Paraguay",
                            "Uruguay": "Uruguay",
                            "Montevideo": "Uruguay",
                            "Chile": "Chile",
                            "Santiago": "Chile"
                        }
                        pais_detectado = "Exterior"
                        for patron, pais in paises.items():
                            if patron.lower() in localidad.lower():
                                pais_detectado = pais
                                break
                        valor = valor_template.replace("{pais_detectado}", pais_detectado)
                    else:
                        valor = valor_template
                else:
                    valor = valor_template

                # Actualizar BD
                self.db_conn.execute(
                    f"UPDATE ofertas_nlp SET {campo} = ? WHERE id_oferta = ?",
                    (valor, id_oferta)
                )
                self.db_conn.commit()

                self.correcciones_aplicadas.append({
                    "id_oferta": id_oferta,
                    "campo": campo,
                    "valor_nuevo": valor,
                    "timestamp": datetime.now().isoformat()
                })

                # Marcar como corregido en validation_errors
                self._marcar_error_corregido(id_oferta, error.get("id_regla"))
                return True

            elif funcion == "limpiar_booleanos":
                campos = ejecutar.get("campos", [])
                valores_invalidos = ejecutar.get("valores_invalidos", [])

                for campo in campos:
                    cursor = self.db_conn.execute(
                        f"SELECT {campo} FROM ofertas_nlp WHERE id_oferta = ?",
                        (id_oferta,)
                    )
                    row = cursor.fetchone()
                    if row and row[0] in valores_invalidos:
                        self.db_conn.execute(
                            f"UPDATE ofertas_nlp SET {campo} = NULL WHERE id_oferta = ?",
                            (id_oferta,)
                        )

                self.db_conn.commit()

                # Marcar como corregido en validation_errors
                self._marcar_error_corregido(id_oferta, error.get("id_regla"))
                return True

        except Exception as e:
            print(f"Error aplicando auto-correccion a {id_oferta}: {e}")
            return False

        return False

    def _marcar_error_corregido(self, id_oferta: str, error_id: str):
        """
        Marca un error como corregido en la tabla validation_errors.

        Args:
            id_oferta: ID de la oferta
            error_id: ID del error (ej: V02_isco_nulo_score_bajo)
        """
        if not self.db_conn:
            return

        try:
            self.db_conn.execute('''
                UPDATE validation_errors
                SET corregido = 1,
                    corregido_timestamp = ?,
                    corregido_metodo = 'auto',
                    resuelto = 1
                WHERE id_oferta = ? AND error_id = ? AND corregido = 0
            ''', (datetime.now().isoformat(), str(id_oferta), error_id))
            self.db_conn.commit()
        except Exception as e:
            print(f"  WARN: Error actualizando validation_errors para {id_oferta}: {e}")

    def _marcar_error_escalado(self, id_oferta: str, error_id: str):
        """
        Marca un error como escalado a Claude en la tabla validation_errors.

        Args:
            id_oferta: ID de la oferta
            error_id: ID del error
        """
        if not self.db_conn:
            return

        try:
            self.db_conn.execute('''
                UPDATE validation_errors
                SET escalado_claude = 1
                WHERE id_oferta = ? AND error_id = ? AND escalado_claude = 0
            ''', (str(id_oferta), error_id))
            self.db_conn.commit()
        except Exception as e:
            print(f"  WARN: Error actualizando escalado_claude para {id_oferta}: {e}")

    def _buscar_config_existente(self, error: Dict, config: Dict) -> bool:
        """
        Busca si existe una regla aplicable en el config indicado.

        Args:
            error: Error detectado
            config: Config de correccion con ruta al archivo

        Returns:
            True si existe una regla aplicable
        """
        config_path = self.config_dir.parent / config.get("config", "")
        if not config_path.exists():
            return False

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            seccion = config.get("buscar_en", "")
            # Navegar a la seccion
            parts = seccion.split(".")
            data = config_data
            for part in parts:
                if isinstance(data, dict) and part in data:
                    data = data[part]
                else:
                    return False

            # Verificar si hay reglas (simplificado)
            if isinstance(data, list) and len(data) > 0:
                return True

        except Exception:
            pass

        return False

    def _agregar_a_cola_claude(self, id_oferta: str, error: Dict, config: Dict):
        """
        Agrega un error a la cola para analisis de Claude.

        Args:
            id_oferta: ID de la oferta
            error: Error detectado
            config: Config de correccion
        """
        diagnostico = error.get("diagnostico")

        # Obtener datos adicionales si es necesario
        datos = {
            "id_oferta": id_oferta,
            "diagnostico": diagnostico,
            "campo": error.get("campo"),
            "mensaje": error.get("mensaje"),
            "config_afectado": config.get("config"),
            "timestamp": datetime.now().isoformat()
        }

        # Agregar datos extra de la oferta si tenemos conexion BD
        if self.db_conn:
            try:
                cursor = self.db_conn.execute("""
                    SELECT
                        n.titulo_limpio,
                        n.area_funcional,
                        n.nivel_seniority,
                        n.sector_empresa,
                        m.isco_code,
                        m.esco_label,
                        m.match_score
                    FROM ofertas_nlp n
                    LEFT JOIN ofertas_esco_matching m ON n.id_oferta = m.id_oferta
                    WHERE n.id_oferta = ?
                """, (id_oferta,))
                row = cursor.fetchone()
                if row:
                    datos.update({
                        "titulo_limpio": row[0],
                        "area_funcional": row[1],
                        "nivel_seniority": row[2],
                        "sector_empresa": row[3],
                        "isco_code": row[4],
                        "esco_label": row[5],
                        "match_score": row[6]
                    })
            except Exception:
                pass

        self.cola_claude[diagnostico].append(datos)

        # Marcar como escalado en validation_errors
        self._marcar_error_escalado(id_oferta, error.get("id_regla"))

    def _generar_patrones_claude(self) -> List[Dict]:
        """
        Genera patrones agrupados para presentar a Claude.

        Returns:
            Lista de patrones con ejemplos agrupados
        """
        umbral = self.correction_map.get("umbrales_escalamiento", {}).get("minimo_casos_para_patron", 3)
        patrones = []

        for diagnostico, casos in self.cola_claude.items():
            if len(casos) >= umbral:
                # Agrupar por similitud
                patron = {
                    "diagnostico": diagnostico,
                    "cantidad": len(casos),
                    "ejemplos": casos[:5],  # Max 5 ejemplos
                    "ids": [c["id_oferta"] for c in casos],
                    "config_afectado": casos[0].get("config_afectado") if casos else None,
                    "accion_requerida": f"Crear regla para resolver {len(casos)} casos de {diagnostico}"
                }
                patrones.append(patron)

        return sorted(patrones, key=lambda x: x["cantidad"], reverse=True)

    def obtener_reporte_claude(self) -> str:
        """
        Genera reporte formateado para Claude.

        Returns:
            Texto con patrones agrupados listo para presentar
        """
        patrones = self._generar_patrones_claude()

        if not patrones:
            return "No hay errores que requieran intervencion de Claude."

        lineas = [
            "="*60,
            "PATRONES PARA ANALISIS DE CLAUDE",
            "="*60,
            ""
        ]

        for i, patron in enumerate(patrones, 1):
            lineas.append(f"## PATRON {i}: {patron['diagnostico']}")
            lineas.append(f"   Cantidad: {patron['cantidad']} ofertas")
            lineas.append(f"   Config: {patron['config_afectado']}")
            lineas.append("")
            lineas.append("   Ejemplos:")

            for ej in patron["ejemplos"][:3]:
                lineas.append(f"   - ID {ej['id_oferta']}: {ej.get('titulo_limpio', 'N/A')}")
                if ej.get("isco_code"):
                    lineas.append(f"     ISCO actual: {ej['isco_code']} - {ej.get('esco_label', '')}")

            lineas.append("")
            lineas.append(f"   ACCION: {patron['accion_requerida']}")
            lineas.append("-"*60)
            lineas.append("")

        return "\n".join(lineas)

    def guardar_cola_claude(self, output_path: Optional[Path] = None) -> Path:
        """
        Guarda la cola de errores para Claude en un archivo JSON.

        Args:
            output_path: Path para guardar. Default: metrics/cola_claude_{timestamp}.json

        Returns:
            Path del archivo guardado
        """
        if output_path is None:
            metrics_dir = self.config_dir.parent / "metrics"
            metrics_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = metrics_dir / f"cola_claude_{timestamp}.json"

        data = {
            "timestamp": datetime.now().isoformat(),
            "patrones": self._generar_patrones_claude(),
            "detalle_por_diagnostico": dict(self.cola_claude),
            "correcciones_aplicadas": self.correcciones_aplicadas
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        return output_path


def procesar_validacion_completa(db_path: str = None, limit: int = None, ids: List[str] = None) -> Dict:
    """
    Ejecuta validacion + correccion completa.

    Args:
        db_path: Path a la BD
        limit: Limite de ofertas
        ids: IDs especificos

    Returns:
        Resultados de validacion y correccion
    """
    from database.auto_validator import validar_ofertas_desde_bd

    # Paso 1: Validar
    print("Paso 1: Validando ofertas...")
    resultados_validacion = validar_ofertas_desde_bd(db_path=db_path, limit=limit, ids=ids)

    print(f"  - Total: {resultados_validacion['total']}")
    print(f"  - Con errores: {resultados_validacion['con_errores']}")

    if resultados_validacion['con_errores'] == 0:
        print("\nNo hay errores que corregir.")
        return {"validacion": resultados_validacion, "correccion": None}

    # Paso 2: Corregir
    print("\nPaso 2: Aplicando correcciones...")

    if db_path is None:
        db_path = str(Path(__file__).parent / "bumeran_scraping.db")

    conn = sqlite3.connect(db_path)
    corrector = AutoCorrector(db_conn=conn)

    resultados_correccion = corrector.procesar_errores(resultados_validacion)
    conn.close()

    print(f"  - Auto-corregidos: {len(resultados_correccion['auto_corregidos'])}")
    print(f"  - Escalados a Claude: {len(resultados_correccion['escalados_claude'])}")
    print(f"  - Sin accion: {len(resultados_correccion['sin_accion'])}")

    if resultados_correccion['patrones_para_claude']:
        print("\n" + corrector.obtener_reporte_claude())
        output_path = corrector.guardar_cola_claude()
        print(f"\nCola para Claude guardada en: {output_path}")

    return {
        "validacion": resultados_validacion,
        "correccion": resultados_correccion
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Auto-corrector MOL")
    parser.add_argument("--limit", type=int, help="Limite de ofertas")
    parser.add_argument("--ids", help="IDs separados por coma")

    args = parser.parse_args()
    ids = args.ids.split(",") if args.ids else None

    resultados = procesar_validacion_completa(limit=args.limit, ids=ids)
