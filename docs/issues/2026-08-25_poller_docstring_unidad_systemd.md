# El docstring del poller apunta a un servicio systemd que no existe

**Detectado:** 2026-08-25, durante el fix de la doble ejecución del scraping.
**Estado:** abierto, sin agendar.
**Severidad:** baja — es documentación desalineada, no un problema operativo.
**NO se arregla en `fix/scraping-doble-ejecucion`.**

> **Nota sobre este documento.** La primera versión afirmaba que el poller corría
> sin supervisión y que un reboot del VPS dejaría mudo el disparo manual del
> dashboard. **Eso era falso**, y el propio error que lo produjo es lo que este
> issue documenta: busqué la unidad systemd por el nombre que da el docstring
> (`vps_command_poller.service`), no la encontré, y concluí que no existía. La
> unidad real existe, se llama distinto y funciona bien.

## Qué pasa

`scripts/vps_command_poller.py` dice en su docstring:

```
Instalar como servicio systemd:
    sudo cp scripts/vps_command_poller.service /etc/systemd/system/
    sudo systemctl enable vps_command_poller
    sudo systemctl start vps_command_poller
```

Dos cosas de esas tres líneas no son ciertas:

1. **`scripts/vps_command_poller.service` no existe en el repo.** El `sudo cp` copiaría
   un archivo inexistente.
2. **La unidad instalada en el VPS se llama `mol-command-poller`, no `vps_command_poller`.**
   Un `systemctl status vps_command_poller` responde `Unit could not be found`, que se lee
   como "no hay supervisión" cuando en realidad la hay.

Lo que sí está instalado y funcionando (`/etc/systemd/system/mol-command-poller.service`):

```ini
[Unit]
Description=MOL VPS Command Poller
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/mol
ExecStart=/usr/bin/python3 /opt/mol/scripts/vps_command_poller.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Estado verificado el 2026-08-25: `enabled` (arranca al bootear) y `active`. Probado con
`systemctl kill -s SIGKILL mol-command-poller`: vuelve solo a los 30 s (`RestartSec`).

## Por qué importa

No hay riesgo operativo: el poller está supervisado, sobrevive a reboots y se relanza si
crashea. El costo es de diagnóstico — el docstring manda a buscar un nombre equivocado, y
alguien que verifique el estado del sistema siguiéndolo concluye que falta supervisión que
sí está. Ya pasó una vez, el 2026-08-25.

Riesgo secundario, más concreto: quien lea el docstring y *actúe* sobre él puede intentar
levantar el poller a mano, quedando **dos instancias** — la de systemd y la manual. Dos
pollers compiten por la misma cola: ambos hacen `poll_once()` sobre `estado='pendiente'`
sin transacción ni lock, así que pueden levantar el mismo comando y ejecutarlo dos veces.
Esto también ocurrió el 2026-08-25 al reiniciar el poller: cada `kill` era revertido por
`Restart=always` a los 30 s, y el relanzamiento manual quedaba encima del que systemd ya
había revivido.

## Arreglo propuesto

1. **Corregir el docstring** de `scripts/vps_command_poller.py` para que nombre la unidad
   real y describa la operación correcta:

```
Servicio systemd (ya instalado en el VPS): mol-command-poller.service

    systemctl status mol-command-poller
    systemctl restart mol-command-poller     # NO relanzar a mano: Restart=always
    journalctl -u mol-command-poller -f      # logs

NO lanzar el poller manualmente: systemd ya mantiene exactamente una
instancia. Un proceso manual queda ENCIMA del de systemd y ambos compiten
por la misma cola de scraping_commands.
```

2. **Versionar el unit file** en el repo como `scripts/mol-command-poller.service`, con el
   contenido real del VPS, para que la configuración deje de existir solo en la máquina.
   Dos mejoras menores al copiarlo:
   - `Environment=PYTHONUNBUFFERED=1` — hoy la salida del poller llega a journald en
     bloques por el buffer de Python.
   - `User=root` explícito (hoy es implícito).

3. Al tocar el unit: `systemctl daemon-reload && systemctl restart mol-command-poller`.

## Verificación posterior

```bash
systemctl is-enabled mol-command-poller     # enabled
systemctl is-active  mol-command-poller     # active
ps -eo cmd | grep -cx "/usr/bin/python3 /opt/mol/scripts/vps_command_poller.py"   # 1
```

Prueba funcional de punta a punta, sin efectos secundarios:

```sql
INSERT INTO scraping_commands (comando, params, creado_por)
VALUES ('pausar_portal', '{"portal":"__healthcheck__"}', 'healthcheck');
```

`pausar_portal` mapea a `log_only()`: no ejecuta ningún scraper, solo recorre el ciclo
`poll_once → process_command → update`. Debe pasar a `completado` en menos de 60 s.

## Nota operativa para quien reinicie el poller

Dos trampas encontradas el 2026-08-25:

- **No usar `pkill -f vps_command_poller`.** El patrón coincide con la propia línea de
  comando del shell remoto de SSH, que se mata a sí mismo a mitad del comando. Usar
  `systemctl restart mol-command-poller`, o matar por PID exacto.
- **No relanzar a mano.** `Restart=always` ya lo hace. Un lanzamiento manual con `&` sobre
  una sesión SSH que se corta además puede forkear de más y dejar procesos huérfanos
  adoptados por init.

## Referencias

- `scripts/vps_command_poller.py` — el poller (docstring a corregir)
- `/etc/systemd/system/mol-command-poller.service` — unidad real, sin versionar
- `fase3_dashboard/sql/022_scraping_commands.sql` — tabla de la cola
- Rama `fix/scraping-doble-ejecucion` — fix de la doble ejecución, donde salió este hallazgo
