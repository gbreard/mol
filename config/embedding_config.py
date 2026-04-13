"""
Configuración centralizada del modelo de embeddings.

Todos los scripts que usen BGE-M3 deben importar desde aquí.
Si cambia el modelo o la revisión, se cambia en un solo lugar.

Uso:
    from config.embedding_config import EMBEDDING_MODEL, EMBEDDING_REVISION
    model = SentenceTransformer(EMBEDDING_MODEL, revision=EMBEDDING_REVISION)
"""

EMBEDDING_MODEL = "BAAI/bge-m3"
EMBEDDING_REVISION = "5617a9f61b028005a4858fdac845db406aefb181"
EMBEDDING_DIMS = 1024
EMBEDDING_NORMALIZE = True
EMBEDDING_BATCH_SIZE = 12

# Cache de equivalencias de skills
EQUIVALENCES_CACHE_TTL_HOURS = 24
EQUIVALENCES_CACHE_PATH = "config/skill_equivalences_lookup.json"
