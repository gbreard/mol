#!/usr/bin/env python3
"""
Calcula tendencias de demanda por ISCO usando regresión lineal robusta.

Normaliza por share de portal (elimina sesgo de nuevas fuentes),
filtra por suficiencia de datos, y proyecta 3 meses.

Uso:
    python scripts/calculate_demand_trends.py          # Calcular y subir a Supabase
    python scripts/calculate_demand_trends.py --dry-run  # Preview sin escribir
    python scripts/calculate_demand_trends.py --months 9  # Ventana de 9 meses

Requisitos:
    pip install supabase numpy scipy

Tabla destino: isco_demand_trend (Supabase)
"""

import sys
import json
import argparse
import logging
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

import numpy as np

# Setup
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# --- Config ---

MIN_MONTHS = 4          # Mínimo meses con datos para estimar
MIN_OFERTAS = 15        # Mínimo ofertas totales
MIN_PORTALES = 1        # Mínimo portales estables
TREND_ALPHA = 0.10      # Significancia para clasificar tendencia
R2_MIN_PROJECTION = 0.3 # R² mínimo para proyectar


def load_supabase_config():
    """Carga config de Supabase."""
    config_path = ROOT / "config" / "supabase_config.json"
    if not config_path.exists():
        # Try env vars
        import os
        url = os.environ.get("SUPABASE_URL") or os.environ.get("NEXT_PUBLIC_SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        if url and key:
            return {"url": url, "service_role_key": key}
        raise FileNotFoundError(f"Config no encontrada: {config_path}")
    return json.load(open(config_path))


def get_supabase_client():
    from supabase import create_client
    config = load_supabase_config()
    return create_client(config["url"], config["service_role_key"])


def fetch_ofertas_data(client, months=6):
    """Fetch ofertas con fecha, isco_code y portal de los últimos N meses."""
    since = (datetime.now() - timedelta(days=months * 31)).strftime("%Y-%m-%d")
    logger.info(f"Fetching ofertas desde {since}...")

    all_data = []
    offset = 0
    batch_size = 1000
    while True:
        result = client.table("ofertas_dashboard") \
            .select("isco_code, fecha_publicacion, portal") \
            .gte("fecha_publicacion", since) \
            .neq("isco_code", "") \
            .range(offset, offset + batch_size - 1) \
            .execute()
        if not result.data:
            break
        all_data.extend(result.data)
        if len(result.data) < batch_size:
            break
        offset += batch_size

    logger.info(f"Fetched {len(all_data)} ofertas")
    return all_data


def build_month_labels(months=6):
    """Genera etiquetas de meses completos (excluye mes actual que está incompleto)."""
    now = datetime.now()
    # Start from last COMPLETE month (not current)
    labels = []
    for i in range(months, 0, -1):
        d = datetime(now.year, now.month, 1) - timedelta(days=i * 30)
        d = datetime(d.year, d.month, 1)
        label = f"{d.year}-{d.month:02d}"
        if label not in labels:
            labels.append(label)
    # Exclude current month
    current = f"{now.year}-{now.month:02d}"
    labels = [l for l in labels if l != current]
    return labels


def find_stable_portals(ofertas, month_labels):
    """Portales presentes en el primer Y último mes."""
    first_month = month_labels[0]
    last_month = month_labels[-1]
    portals_first = set()
    portals_last = set()

    for o in ofertas:
        if not o.get("fecha_publicacion") or not o.get("portal"):
            continue
        m = o["fecha_publicacion"][:7]
        p = o["portal"]
        if m == first_month:
            portals_first.add(p)
        if m == last_month:
            portals_last.add(p)

    stable = portals_first & portals_last
    logger.info(f"Portales estables: {stable} (de {portals_first | portals_last})")
    return stable


def compute_portal_totals(ofertas, month_labels, stable_portals):
    """Total de ofertas por portal por mes (para normalización de share)."""
    totals = defaultdict(lambda: defaultdict(int))
    for o in ofertas:
        if not o.get("fecha_publicacion") or not o.get("portal"):
            continue
        p = o["portal"]
        if p not in stable_portals:
            continue
        m = o["fecha_publicacion"][:7]
        if m in month_labels:
            totals[p][m] += 1
    return totals


def linear_regression(x, y):
    """Regresión lineal simple. Retorna slope, intercept, r2, p_value, se."""
    n = len(x)
    if n < 3:
        return 0, 0, 0, 1.0, 0

    x = np.array(x, dtype=float)
    y = np.array(y, dtype=float)

    x_mean = np.mean(x)
    y_mean = np.mean(y)

    ss_xx = np.sum((x - x_mean) ** 2)
    ss_yy = np.sum((y - y_mean) ** 2)
    ss_xy = np.sum((x - x_mean) * (y - y_mean))

    if ss_xx == 0:
        return 0, y_mean, 0, 1.0, 0

    slope = ss_xy / ss_xx
    intercept = y_mean - slope * x_mean

    y_pred = intercept + slope * x
    ss_res = np.sum((y - y_pred) ** 2)
    r2 = 1 - (ss_res / ss_yy) if ss_yy > 0 else 0
    r2 = max(0, r2)

    # Standard error of slope + t-test p-value
    if n > 2 and ss_xx > 0:
        mse = ss_res / (n - 2)
        se_slope = np.sqrt(mse / ss_xx) if mse > 0 else 0
        if se_slope > 0:
            t_stat = slope / se_slope
            # Approximate p-value using t-distribution (scipy-free)
            # Use normal approximation for n >= 6
            p_value = 2 * (1 - _normal_cdf(abs(t_stat)))
        else:
            p_value = 1.0
    else:
        se_slope = 0
        p_value = 1.0

    return slope, intercept, r2, p_value, se_slope


def _normal_cdf(x):
    """Approximate CDF of standard normal (Abramowitz & Stegun)."""
    # Good to ~1e-7 accuracy
    t = 1.0 / (1.0 + 0.2316419 * abs(x))
    d = 0.3989422804014327  # 1/sqrt(2*pi)
    p = d * np.exp(-x * x / 2.0) * (
        t * (0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429))))
    )
    return 1.0 - p if x >= 0 else p


def calculate_trends(ofertas, month_labels, stable_portals):
    """Calcula tendencia por ISCO."""
    use_all = len(stable_portals) == 0
    portal_totals = compute_portal_totals(ofertas, month_labels, stable_portals)

    # Group by ISCO
    by_isco = defaultdict(list)
    for o in ofertas:
        if o.get("isco_code"):
            by_isco[o["isco_code"]].append(o)

    results = []

    for isco_code, isco_ofertas in by_isco.items():
        total = len(isco_ofertas)

        # Monthly raw counts (for sparkline)
        raw_monthly = {m: 0 for m in month_labels}
        for o in isco_ofertas:
            if o.get("fecha_publicacion"):
                m = o["fecha_publicacion"][:7]
                if m in raw_monthly:
                    raw_monthly[m] += 1

        monthly_counts = [raw_monthly[m] for m in month_labels]
        meses_con_datos = sum(1 for c in monthly_counts if c > 0)

        # Check sufficiency
        suficiente = (
            meses_con_datos >= MIN_MONTHS
            and total >= MIN_OFERTAS
            and (use_all or len(stable_portals) >= MIN_PORTALES)
        )

        if not suficiente:
            results.append({
                "isco_code": isco_code,
                "trend_slope": None,
                "trend_pvalue": None,
                "trend_r2": None,
                "trend_label": "insuficiente",
                "volatility_cv": None,
                "volatility_label": None,
                "ofertas_total": total,
                "meses_con_datos": meses_con_datos,
                "portales_usados": len(stable_portals) if not use_all else 0,
                "proyeccion_3m": None,
                "proyeccion_ci": None,
                "monthly_counts": monthly_counts,
                "monthly_labels": month_labels,
                "suficiente": False,
            })
            continue

        # Calculate normalized share per month
        # For each stable portal: share = isco_ofertas_in_portal_month / total_portal_month
        # Average across portals = normalized share
        if use_all:
            # No normalization possible — use raw counts
            share_series = [float(c) for c in monthly_counts]
        else:
            share_by_month = []
            for m in month_labels:
                portal_shares = []
                for portal in stable_portals:
                    pt = portal_totals[portal].get(m, 0)
                    if pt == 0:
                        continue
                    # Count this ISCO in this portal+month
                    isco_in_pm = sum(
                        1 for o in isco_ofertas
                        if o.get("portal") == portal
                        and o.get("fecha_publicacion", "")[:7] == m
                    )
                    portal_shares.append(isco_in_pm / pt)
                share_by_month.append(np.mean(portal_shares) if portal_shares else 0)
            share_series = share_by_month

        # Linear regression on share series
        x = list(range(len(share_series)))
        slope, intercept, r2, p_value, se_slope = linear_regression(x, share_series)

        # Classify trend with consistency check
        if p_value < TREND_ALPHA and slope > 0:
            trend_label = "creciendo"
        elif p_value < TREND_ALPHA and slope < 0:
            trend_label = "cayendo"
        else:
            trend_label = "estable"

        # Consistency check: if "creciendo" but last month dropped >50% vs peak,
        # or if driven by a single spike, override to "estable"
        if trend_label != "estable" and len(share_series) >= 3:
            last = share_series[-1]
            peak = max(share_series)
            median_val = float(np.median(share_series))
            # If peak is >3x the median, it's a spike — don't trust the trend
            if peak > 0 and peak > 3 * median_val and median_val > 0:
                trend_label = "estable"
            # If "creciendo" but last month < median, not convincing
            elif trend_label == "creciendo" and last < median_val * 0.7:
                trend_label = "estable"
            # If "cayendo" but last month > median, not convincing
            elif trend_label == "cayendo" and last > median_val * 1.3:
                trend_label = "estable"

        # Volatility from residuals
        y_pred = [intercept + slope * t for t in x]
        residuals = [s - p for s, p in zip(share_series, y_pred)]
        res_nonzero = [r for r in residuals if abs(r) > 1e-10]
        if res_nonzero:
            res_mean = np.mean([abs(r) for r in res_nonzero])
            mean_share = np.mean(share_series) if np.mean(share_series) > 0 else 1
            cv = float(np.std(residuals) / mean_share * 100) if mean_share > 0 else 0
        else:
            cv = 0

        if cv > 60:
            vol_label = "volatil"
        elif cv > 30:
            vol_label = "variable"
        else:
            vol_label = "estable"

        # Projection: 3 months ahead
        proj_3m = None
        proj_ci = None
        if r2 >= R2_MIN_PROJECTION:
            n = len(share_series)
            proj_3m = float(intercept + slope * (n + 2))  # 3 months ahead (0-indexed)
            proj_3m = max(0, proj_3m)
            if se_slope > 0:
                proj_ci = float(1.96 * se_slope * (n + 2))
            else:
                proj_ci = None

        results.append({
            "isco_code": isco_code,
            "trend_slope": round(float(slope), 8) if slope else 0,
            "trend_pvalue": round(float(p_value), 4),
            "trend_r2": round(float(r2), 4),
            "trend_label": trend_label,
            "volatility_cv": round(cv, 1),
            "volatility_label": vol_label,
            "ofertas_total": total,
            "meses_con_datos": meses_con_datos,
            "portales_usados": len(stable_portals) if not use_all else 0,
            "proyeccion_3m": round(proj_3m, 6) if proj_3m is not None else None,
            "proyeccion_ci": round(proj_ci, 6) if proj_ci is not None else None,
            "monthly_counts": monthly_counts,
            "monthly_labels": month_labels,
            "suficiente": True,
        })

    return results


def upload_to_supabase(client, results, dry_run=False):
    """Upsert results to isco_demand_trend table."""
    now = datetime.now().isoformat()

    rows = []
    for r in results:
        rows.append({
            "isco_code": r["isco_code"],
            "trend_slope": r["trend_slope"],
            "trend_pvalue": r["trend_pvalue"],
            "trend_r2": r["trend_r2"],
            "trend_label": r["trend_label"],
            "volatility_cv": r["volatility_cv"],
            "volatility_label": r["volatility_label"],
            "ofertas_total": r["ofertas_total"],
            "meses_con_datos": r["meses_con_datos"],
            "portales_usados": r["portales_usados"],
            "proyeccion_3m": r["proyeccion_3m"],
            "proyeccion_ci": r["proyeccion_ci"],
            "monthly_counts": json.dumps(r["monthly_counts"]),
            "monthly_labels": json.dumps(r["monthly_labels"]),
            "suficiente": r["suficiente"],
            "calculated_at": now,
        })

    if dry_run:
        logger.info(f"DRY RUN: {len(rows)} rows would be upserted")
        return

    # Upsert in batches of 100
    for i in range(0, len(rows), 100):
        batch = rows[i:i + 100]
        client.table("isco_demand_trend").upsert(batch, on_conflict="isco_code").execute()
        logger.info(f"  Upserted {i + len(batch)}/{len(rows)}")

    logger.info(f"Upload complete: {len(rows)} ISCOs")


def print_summary(results):
    """Print summary statistics."""
    total = len(results)
    suficientes = [r for r in results if r["suficiente"]]
    insuficientes = total - len(suficientes)

    creciendo = sum(1 for r in suficientes if r["trend_label"] == "creciendo")
    estable = sum(1 for r in suficientes if r["trend_label"] == "estable")
    cayendo = sum(1 for r in suficientes if r["trend_label"] == "cayendo")

    estable_vol = sum(1 for r in suficientes if r["volatility_label"] == "estable")
    variable_vol = sum(1 for r in suficientes if r["volatility_label"] == "variable")
    volatil_vol = sum(1 for r in suficientes if r["volatility_label"] == "volatil")

    print(f"\n{'='*50}")
    print(f"DEMAND TREND ANALYSIS")
    print(f"{'='*50}")
    print(f"Total ISCOs analizados: {total}")
    print(f"  Con datos suficientes: {len(suficientes)}")
    print(f"  Datos insuficientes:   {insuficientes}")
    print()
    print(f"Tendencia (n={len(suficientes)}):")
    print(f"  ↑ Creciendo: {creciendo} ({creciendo/len(suficientes)*100:.0f}%)" if suficientes else "")
    print(f"  → Estable:   {estable} ({estable/len(suficientes)*100:.0f}%)" if suficientes else "")
    print(f"  ↓ Cayendo:   {cayendo} ({cayendo/len(suficientes)*100:.0f}%)" if suficientes else "")
    print()
    print(f"Volatilidad (n={len(suficientes)}):")
    print(f"  Estable:   {estable_vol}")
    print(f"  Variable:  {variable_vol}")
    print(f"  Volátil:   {volatil_vol}")

    # Top 5 growing
    growing = sorted([r for r in suficientes if r["trend_label"] == "creciendo"],
                     key=lambda r: r["trend_slope"] or 0, reverse=True)
    if growing:
        print(f"\nTop 5 creciendo:")
        for r in growing[:5]:
            print(f"  ISCO {r['isco_code']}: slope={r['trend_slope']:.6f} p={r['trend_pvalue']:.3f} R²={r['trend_r2']:.2f} ofertas={r['ofertas_total']}")

    # Top 5 declining
    declining = sorted([r for r in suficientes if r["trend_label"] == "cayendo"],
                       key=lambda r: r["trend_slope"] or 0)
    if declining:
        print(f"\nTop 5 cayendo:")
        for r in declining[:5]:
            print(f"  ISCO {r['isco_code']}: slope={r['trend_slope']:.6f} p={r['trend_pvalue']:.3f} R²={r['trend_r2']:.2f} ofertas={r['ofertas_total']}")

    print(f"{'='*50}\n")


def main():
    parser = argparse.ArgumentParser(description="Calcula tendencias de demanda por ISCO")
    parser.add_argument("--dry-run", action="store_true", help="Preview sin escribir")
    parser.add_argument("--months", type=int, default=6, help="Ventana en meses (default: 6)")
    args = parser.parse_args()

    client = get_supabase_client()

    # 1. Fetch data
    ofertas = fetch_ofertas_data(client, months=args.months)
    if not ofertas:
        logger.warning("No hay ofertas en la ventana. Nada que calcular.")
        return

    # 2. Build month window
    month_labels = build_month_labels(months=args.months)
    logger.info(f"Ventana: {month_labels[0]} → {month_labels[-1]} ({len(month_labels)} meses)")

    # 3. Find stable portals
    stable_portals = find_stable_portals(ofertas, month_labels)

    # 4. Calculate trends
    results = calculate_trends(ofertas, month_labels, stable_portals)
    logger.info(f"Calculadas tendencias para {len(results)} ISCOs")

    # 5. Summary
    print_summary(results)

    # 6. Upload
    upload_to_supabase(client, results, dry_run=args.dry_run)

    if args.dry_run:
        logger.info("Dry run completo. Usar sin --dry-run para subir a Supabase.")


if __name__ == "__main__":
    main()
