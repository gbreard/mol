#!/usr/bin/env python3
"""
Indeed Argentina - Scraping LOCAL
=================================

Wrapper sobre run_indeed_vps.py para ejecución local.
Usa delays más conservadores (4s) para evitar bloqueo de Cloudflare.

Invocado por pipeline_command_poller.py cuando el admin lanza 'scrape_indeed'.

Uso directo:
    python3 scripts/scraping/run_indeed_local.py
    python3 scripts/scraping/run_indeed_local.py --delay 4 --detail-delay 4
    python3 scripts/scraping/run_indeed_local.py --force-chunk 2
    python3 scripts/scraping/run_indeed_local.py --all-keywords
"""

import sys
from pathlib import Path

# Import main() from the VPS script (same logic, same BD path resolution)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_indeed_vps import main

if __name__ == '__main__':
    # If no delay args provided, inject conservative defaults for local
    if '--delay' not in sys.argv:
        sys.argv.extend(['--delay', '4'])
    if '--detail-delay' not in sys.argv:
        sys.argv.extend(['--detail-delay', '4'])
    main()
