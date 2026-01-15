#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick test runner for v3 Gold Set validation."""

import sys
import io
import os

# Force UTF-8 output
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Set working directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("Starting test...")

try:
    from test_gold_set_v3 import test_gold_set
    correctos, total = test_gold_set()
    print(f"\n\nFINAL: {correctos}/{total}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
