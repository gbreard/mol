# -*- coding: utf-8 -*-
"""
Corrige provincia/localidad según reglas de nlp_normalization.json

Reglas principales:
- "Capital Federal" en provincia -> "CABA"
- "Capital Federal" en localidad -> null, provincia = "CABA"
- Localidad con sufijo ", CABA" -> quitar sufijo, provincia = "CABA"
- Si localidad es barrio de CABA y provincia = Buenos Aires -> provincia = "CABA"
"""
import sqlite3
import json
from pathlib import Path

BASE = Path(__file__).parent.parent
DB_PATH = BASE / "database" / "bumeran_scraping.db"
CONFIG_PATH = BASE / "config" / "nlp_normalization.json"
GOLD_SET_PATH = BASE / "database" / "gold_set_nlp_100_ids.json"


def cargar_config():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def corregir_ubicacion(provincia, localidad, config):
    """
    Aplica reglas de corrección a provincia/localidad.
    Retorna (provincia_corregida, localidad_corregida, cambios)
    """
    cambios = []
    prov_orig, loc_orig = provincia, localidad

    correccion = config.get("correccion_ubicacion", {})
    barrios_caba = [b.lower() for b in correccion.get("barrios_caba", [])]

    # Normalizar provincia según mapeo
    mapeo_prov = config.get("provincia", {}).get("mapeo", {})
    if provincia and provincia in mapeo_prov:
        provincia = mapeo_prov[provincia]
        cambios.append(f"provincia: {prov_orig} -> {provincia}")

    # Limpiar sufijos de localidad
    sufijos = config.get("localidad", {}).get("limpiar_sufijos", [])
    if localidad:
        for sufijo in sufijos:
            if localidad.endswith(sufijo):
                localidad = localidad[:-len(sufijo)].strip()
                provincia = "CABA"
                cambios.append(f"localidad sufijo {sufijo} removido")

    # Si localidad = "Capital Federal", convertir a null y provincia = CABA
    if localidad and localidad.lower() == "capital federal":
        provincia = "CABA"
        localidad = None
        cambios.append("localidad Capital Federal -> null, provincia -> CABA")

    # Si localidad es barrio de CABA y provincia = Buenos Aires, corregir
    if localidad and provincia == "Buenos Aires":
        loc_lower = localidad.lower().strip()
        # Buscar coincidencia parcial (por si tiene variantes)
        for barrio in barrios_caba:
            if barrio in loc_lower or loc_lower in barrio:
                provincia = "CABA"
                cambios.append(f"localidad {localidad} es barrio CABA -> provincia CABA")
                break

    return provincia, localidad, cambios


def corregir_gold_set(dry_run=True):
    """Corrige ubicación en ofertas del Gold Set."""
    config = cargar_config()

    # Cargar IDs
    with open(GOLD_SET_PATH, 'r', encoding='utf-8') as f:
        ids = json.load(f)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    placeholders = ','.join(['?' for _ in ids])
    c.execute(f"""
        SELECT id_oferta, provincia, localidad
        FROM ofertas_nlp
        WHERE id_oferta IN ({placeholders})
    """, ids)

    correcciones = []
    for row in c.fetchall():
        id_oferta, prov, loc = row
        prov_new, loc_new, cambios = corregir_ubicacion(prov, loc, config)

        if cambios:
            correcciones.append({
                'id': id_oferta,
                'prov_orig': prov,
                'loc_orig': loc,
                'prov_new': prov_new,
                'loc_new': loc_new,
                'cambios': cambios
            })

    print(f"Correcciones a aplicar: {len(correcciones)}")
    print("-" * 70)

    for corr in correcciones[:15]:  # Mostrar primeros 15
        print(f"{corr['id']}:")
        print(f"  ANTES:  provincia={corr['prov_orig']}, localidad={corr['loc_orig']}")
        print(f"  DESPUES: provincia={corr['prov_new']}, localidad={corr['loc_new']}")
        print(f"  Cambios: {', '.join(corr['cambios'])}")
        print()

    if len(correcciones) > 15:
        print(f"... y {len(correcciones) - 15} más")

    if dry_run:
        print(f"\n[DRY RUN] No se modificó la BD. Usar dry_run=False para aplicar.")
        conn.close()
        return correcciones

    # Aplicar cambios
    print("\nAplicando cambios...")
    for corr in correcciones:
        c.execute("""
            UPDATE ofertas_nlp
            SET provincia = ?, localidad = ?
            WHERE id_oferta = ?
        """, (corr['prov_new'], corr['loc_new'], corr['id']))

    conn.commit()
    print(f"[OK] {len(correcciones)} registros corregidos")
    conn.close()

    return correcciones


if __name__ == "__main__":
    import sys
    dry_run = "--apply" not in sys.argv
    corregir_gold_set(dry_run=dry_run)
