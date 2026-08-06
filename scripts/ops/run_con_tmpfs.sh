#!/bin/bash
# run_con_tmpfs.sh — corre un comando con la BD en tmpfs (RAM) y sync-back verificado.
#
# Institucionaliza el patron del incidente 9p (FRENTE D, jul/2026): el drvfs de WSL
# se cuelga en pread bajo carga sostenida (wchan p9_client_rpc); con la BD en tmpfs
# el mismo matching que se colgaba siempre corre en 40-60 min por tanda.
#
# Uso:  scripts/ops/run_con_tmpfs.sh <comando...>
#   ej: scripts/ops/run_con_tmpfs.sh python scripts/run_validated_pipeline.py --limit 2000
#
# Hace: verifica espacio y BD libre -> copia BD a /dev/shm (sha256) -> symlink en
# database/ -> ejecuta el comando -> checkpoint WAL -> sync-back a D: (sha256
# verificado) -> restaura el archivo real -> desmonta. Aborta limpio ante cualquier
# verificacion fallida. La BD original queda como .bak_tmpfs hasta el final.
set -euo pipefail

REPO="$(cd "$(dirname "$0")/../.." && pwd)"
DB="$REPO/database/bumeran_scraping.db"
RAMDIR=/dev/shm/mol_db
RAMDB="$RAMDIR/bumeran_scraping.db"
BAK="$DB.bak_tmpfs"

die() { echo "[run_con_tmpfs] ABORT: $*" >&2; exit 1; }

[ $# -ge 1 ] || die "falta el comando a ejecutar"
[ -f "$DB" ] || die "BD no encontrada: $DB"
[ -L "$DB" ] && die "la BD ya es un symlink (otra corrida tmpfs activa?)"

# BD no en uso (write-lock inmediato)
/usr/bin/python3 - "$DB" <<'PY' || die "la BD esta en uso (write-lock ocupado)"
import sqlite3, sys
c = sqlite3.connect(sys.argv[1], timeout=5)
c.execute('BEGIN IMMEDIATE'); c.rollback()
PY

# espacio en /dev/shm: tamano BD + 25% margen
NEED=$(( $(stat -c %s "$DB") * 5 / 4 ))
AVAIL=$(( $(df --output=avail -B1 /dev/shm | tail -1) ))
[ "$AVAIL" -gt "$NEED" ] || die "espacio insuficiente en /dev/shm ($AVAIL < $NEED)"

mkdir -p "$RAMDIR"
echo "[run_con_tmpfs] copiando BD a tmpfs..."
cp "$DB" "$RAMDB"
H1=$(sha256sum "$DB" | cut -d' ' -f1)
H2=$(sha256sum "$RAMDB" | cut -d' ' -f1)
[ "$H1" = "$H2" ] || { rm -rf "$RAMDIR"; die "hash de copia no coincide"; }

mv "$DB" "$BAK"
ln -s "$RAMDB" "$DB"
echo "[run_con_tmpfs] BD en tmpfs, symlink activo. Ejecutando: $*"

restaurar() {
  set +e
  echo "[run_con_tmpfs] cierre: checkpoint + sync-back..."
  /usr/bin/python3 - "$RAMDB" <<'PY'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1], timeout=120)
c.execute('PRAGMA wal_checkpoint(TRUNCATE)')
r = c.execute('PRAGMA quick_check').fetchone()[0]
c.close()
assert r == 'ok', f'quick_check: {r}'
PY
  if [ $? -ne 0 ]; then
    echo "[run_con_tmpfs] ABORT en cierre: integridad tmpfs fallo — BD original intacta en $BAK, tmpfs se conserva en $RAMDB" >&2
    exit 1
  fi
  rm -f "$DB"                       # symlink
  cp "$RAMDB" "$DB.sync_tmp"
  HR=$(sha256sum "$RAMDB" | cut -d' ' -f1)
  HS=$(sha256sum "$DB.sync_tmp" | cut -d' ' -f1)
  if [ "$HR" != "$HS" ]; then
    echo "[run_con_tmpfs] ABORT: hash de sync-back no coincide — tmpfs conservado en $RAMDB, original en $BAK" >&2
    exit 1
  fi
  mv "$DB.sync_tmp" "$DB"
  rm -rf "$RAMDIR"
  echo "[run_con_tmpfs] BD restaurada y verificada en $DB. Backup previo en $BAK (borrarlo a mano tras validar)."
}
trap restaurar EXIT

RC=0
"$@" || RC=$?
echo "[run_con_tmpfs] comando termino rc=$RC"
exit $RC
