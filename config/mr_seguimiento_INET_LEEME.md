# mr_seguimiento_INET.csv — ESPEJO (no es la fuente)

**Fuente:** `D:\OEDE\Voucher\data\mr_seguimiento_INET_2026-08-23.csv`
**Si cambia allá, re-sincronizar acá. MOL consume, Voucher posee.**

Duplicación **consciente y anotada**: evita que MOL dependa de una ruta de otro proyecto que puede
moverse, sin crear una segunda fuente de verdad silenciosa. Cualquier corrección al contenido se
hace en Voucher y se re-copia; no editar este archivo.

## Qué contiene

51 **Marcos de Referencia del INET/CFE** (perfiles ocupacionales oficiales de certificación de
competencias; algunos con el número de resolución CFE en el nombre — 108/10, 204/13) mapeados al
vocabulario de MOL: `esco_code`, `isco` y el flag `canon` (39 exacto · 9 aprox · 2 SIN CANON ·
1 "exacto · CUAR"). Sectores: Construcción 22 · Automotriz 16 · Gastronomía 9 · Textil 4.
Las 2 filas SIN CANON van con `esco_code`/`isco` vacíos.

## Procedencia

Cruce manual ad-hoc de junio 2026, cargado directo como tabla dentro del SQLite de la base de
colegas del VPS (`/srv/datasette/colegas.sqlite`); sin archivo fuente en ningún repo. Recuperado
del VPS el 2026-08-23, antes de que la publicación post-L sobrescribiera esa única copia.
Procedencia completa en el LEEME de la fuente (`Voucher/data/mr_seguimiento_INET_LEEME.md`).

Sirve como puente MOL ↔ formación profesional: mirar la demanda laboral por la lente de los
Marcos de Referencia que se financian o se siguen.
