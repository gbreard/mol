#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script temporal para ejecutar scraping semanal"""
import sys
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "01_sources" / "bumeran" / "scrapers"))
sys.path.insert(0, str(PROJECT_ROOT))

# Execute
from run_scheduler import ejecutar_scraping
ejecutar_scraping()
