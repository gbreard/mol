# -*- coding: utf-8 -*-
"""
MOL - Test Suite
================

Estructura de tests para el Monitor de Ofertas Laborales.

tests/
├── conftest.py          # Fixtures compartidos
├── matching/            # Tests de matching ESCO
│   ├── gold_set.json    # Gold set de matching
│   └── test_precision.py
├── nlp/                 # Tests de extracción NLP
│   ├── gold_set.json    # Gold set de NLP (futuro)
│   └── test_extraction.py
└── integration/         # Tests end-to-end
    └── test_pipeline.py

Ejecución:
    pytest tests/ -v
    pytest tests/matching/ -v
    pytest tests/nlp/ -v
"""
