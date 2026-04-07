# VPS-BGE-M3-EMBED — Servidor de embeddings BGE-M3 en VPS

## Contexto

El pipeline de extracción de skills desde texto libre necesita generar
embeddings con el mismo modelo (BAAI/bge-m3, sentence-transformers) que
se usó para generar skills_embeddings en Supabase. Esto permite cosine
similarity real contra los 14,247 skills ESCO completos.

El VPS Hostinger ya tiene Python 3.12, 7.1GB RAM libre y puerto 8082 disponible.

---

## Parte 1 — Servidor de embeddings en el VPS

### Instalación

```bash
pip3 install fastapi uvicorn sentence-transformers torch --break-system-packages
```

### Archivo embed_server.py

Crear en el VPS en `/home/scraper/embed_server.py` (o donde viva el scraper):

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="BGE-M3 Embed Server")

# Cargar modelo al iniciar (una sola vez)
logger.info("Cargando modelo BAAI/bge-m3...")
model = SentenceTransformer("BAAI/bge-m3")
logger.info("Modelo listo.")

class EmbedRequest(BaseModel):
    text: str
    texts: list[str] = []  # batch opcional

class EmbedResponse(BaseModel):
    embedding: list[float] | None = None
    embeddings: list[list[float]] | None = None
    dims: int

@app.get("/health")
def health():
    return {"status": "ok", "model": "BAAI/bge-m3", "dims": 1024}

@app.post("/embed", response_model=EmbedResponse)
def embed(req: EmbedRequest):
    try:
        if req.texts:
            # Batch: múltiples textos en una llamada
            vecs = model.encode(req.texts, normalize_embeddings=True)
            return EmbedResponse(
                embeddings=[v.tolist() for v in vecs],
                dims=1024
            )
        elif req.text:
            # Single: un texto
            vec = model.encode(req.text, normalize_embeddings=True)
            return EmbedResponse(embedding=vec.tolist(), dims=1024)
        else:
            raise HTTPException(status_code=400, detail="text o texts requerido")
    except Exception as e:
        logger.error(f"Error generando embedding: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Correr el servidor

```bash
# En el VPS, desde el directorio del scraper:
uvicorn embed_server:app --host 0.0.0.0 --port 8082 --workers 1
```

### Correr como servicio permanente (systemd)

```bash
# Crear /etc/systemd/system/embed-server.service
[Unit]
Description=BGE-M3 Embed Server
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/home/scraper
ExecStart=/usr/bin/python3 -m uvicorn embed_server:app --host 0.0.0.0 --port 8082 --workers 1
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target

# Activar:
systemctl daemon-reload
systemctl enable embed-server
systemctl start embed-server
```

### Verificar

```bash
# Desde el VPS:
curl http://localhost:8082/health

# Test de embedding:
curl -X POST http://localhost:8082/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "administrar medicación"}'
# Debe retornar array de 1024 floats

# Test batch:
curl -X POST http://localhost:8082/embed \
  -H "Content-Type: application/json" \
  -d '{"texts": ["administrar medicación", "albañilería", "Python"]}'
```

### Seguridad mínima

El endpoint es público en el puerto 8082. Agregar un token simple:

```python
# En embed_server.py, agregar header check:
from fastapi import Header

EMBED_SECRET = os.environ.get("EMBED_SECRET", "cambiar-esto")

@app.post("/embed")
def embed(req: EmbedRequest, x_embed_secret: str = Header(None)):
    if x_embed_secret != EMBED_SECRET:
        raise HTTPException(status_code=401, detail="No autorizado")
    # ... resto del código
```

Agregar `EMBED_SECRET` en variables de entorno del VPS y en Vercel.

---

## Parte 2 — Cambios en /api/skills-extract-from-text

### Nuevo pipeline completo

```
Texto libre
    ↓
Groq → 5-8 keywords técnicas (~0.3s)
    ↓
VPS BGE-M3 → embeddings batch de todas las keywords (~0.6s)
    ↓
Supabase pgvector → top 5 skills por keyword en paralelo (~0.3s)
    ↓
Groq → selecciona las relevantes del resultado (~0.4s)
    ↓
Total: ~1.5s
```

### Función embedTexts en la API de Vercel

```typescript
const VPS_EMBED_URL = process.env.VPS_EMBED_URL  // ej: http://IP:8082
const VPS_EMBED_SECRET = process.env.VPS_EMBED_SECRET

async function embedTexts(texts: string[]): Promise<number[][]> {
  const res = await fetch(`${VPS_EMBED_URL}/embed`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-embed-secret': VPS_EMBED_SECRET ?? ''
    },
    body: JSON.stringify({ texts }),
    signal: AbortSignal.timeout(5000)  // timeout 5s
  })
  
  if (!res.ok) throw new Error(`Embed server error: ${res.status}`)
  
  const data = await res.json()
  return data.embeddings  // array de arrays de 1024 floats
}
```

### Búsqueda por vector en Supabase

```typescript
async function searchSkillsByVector(
  embedding: number[],
  limit: number = 5
): Promise<{ skill_uri: string, skill_label: string, similarity: number }[]> {
  const { data } = await supabase.rpc('match_skills_by_embedding', {
    query_embedding: embedding,
    match_threshold: 0.5,
    match_count: limit
  })
  return data ?? []
}
```

**Nueva RPC en Supabase `match_skills_by_embedding`:**

```sql
CREATE OR REPLACE FUNCTION match_skills_by_embedding(
  query_embedding  vector(1024),
  match_threshold  FLOAT DEFAULT 0.5,
  match_count      INT   DEFAULT 5
)
RETURNS TABLE (
  skill_uri    TEXT,
  skill_label  TEXT,
  similarity   FLOAT
)
LANGUAGE sql STABLE
AS $$
  SELECT
    skill_uri,
    skill_label,
    (1 - (embedding <=> query_embedding))::FLOAT AS similarity
  FROM skills_embeddings
  WHERE (1 - (embedding <=> query_embedding)) >= match_threshold
  ORDER BY embedding <=> query_embedding
  LIMIT match_count;
$$;
```

### Pipeline completo en route.ts

```typescript
export async function POST(request: Request) {
  const { text } = await request.json()
  
  if (!text?.trim()) return NextResponse.json({ skills: [], method: 'empty' })

  try {
    // PASO 1: Groq genera keywords técnicas
    const keywords = await extractSkillsWithLLM(text)  // ya existe
    if (keywords.length === 0) throw new Error('No keywords')

    // PASO 2: Embeddings batch de todas las keywords (una sola llamada al VPS)
    const embeddings = await embedTexts(keywords)

    // PASO 3: Búsqueda pgvector en paralelo por cada keyword
    const searchResults = await Promise.all(
      embeddings.map(emb => searchSkillsByVector(emb, 5))
    )

    // PASO 4: Deduplicar por URI, tomar los de mayor similarity
    const skillMap = new Map<string, { uri: string, label: string, score: number }>()
    for (const results of searchResults) {
      for (const skill of results) {
        const existing = skillMap.get(skill.skill_uri)
        if (!existing || skill.similarity > existing.score) {
          skillMap.set(skill.skill_uri, {
            uri: skill.skill_uri,
            label: skill.skill_label,
            score: skill.similarity
          })
        }
      }
    }

    const candidates = Array.from(skillMap.values())
      .sort((a, b) => b.score - a.score)
      .slice(0, 30)

    // PASO 5: Groq selecciona las más relevantes del candidato
    const selected = await selectRelevantSkills(text, candidates)  // función existente RAG

    return NextResponse.json({
      skills: selected,
      method: 'llm+bge-m3',
      keywords,
      total_candidates: candidates.length
    })

  } catch (err) {
    // Fallback al pipeline anterior si el VPS no está disponible
    console.error('BGE-M3 fallback:', err)
    return fallbackPipeline(text)  // pipeline LLM + full-text actual
  }
}
```

### Variables de entorno a agregar en Vercel

```
VPS_EMBED_URL=http://[IP_DEL_VPS]:8082
VPS_EMBED_SECRET=[token_secreto]
```

---

## Criterios de aceptación

**VPS:**
- [ ] `curl http://[VPS_IP]:8082/health` retorna `{"status": "ok"}`
- [ ] Embedding de "administrar medicación" retorna array de 1024 floats
- [ ] Batch de 5 textos retorna 5 arrays de 1024 floats
- [ ] Servicio systemd arranca automáticamente al reiniciar el VPS

**RPC Supabase:**
- [ ] `match_skills_by_embedding` retorna skills con similarity > 0.5
- [ ] Para embedding de "administrar medicación" retorna skills de salud

**Pipeline completo:**
- [ ] Texto de enfermería → retorna "administrar la medicación prescrita",
      "monitorizar signos vitales" u equivalentes
- [ ] Texto de construcción → retorna skills de albañilería/construcción
- [ ] Texto de programación → retorna Python, JavaScript, bases de datos
- [ ] Si VPS no disponible → fallback al pipeline anterior sin error 500
- [ ] Tiempo total < 2s con VPS warm

---

## Tests

`tests/vps-embed.test.ts`
- Health check retorna 200
- Embedding retorna 1024 dims
- Batch de 3 textos retorna 3 embeddings

`tests/skills-extract-bge-m3.test.ts`
- Texto enfermería → skills de salud (no "colocar topes")
- Texto construcción → skills de construcción
- VPS timeout → fallback sin error 500
- Texto vacío → array vacío

---

## Notas

- El modelo BGE-M3 tarda ~30s en cargar la primera vez que arranca el servidor.
  El health check confirma que está listo antes de recibir requests.

- Con `--workers 1` el servidor maneja 1 request a la vez. Para el MVP
  con pocas OEs es suficiente. Si hay concurrencia agregar workers o 
  implementar una queue simple.

- El batch endpoint (`texts: string[]`) permite enviar todas las keywords
  de una búsqueda en una sola llamada HTTP en lugar de N llamadas.
  Esto reduce la latencia de red significativamente.

- `EMBED_SECRET` es seguridad mínima — evita que cualquiera use el endpoint.
  No es TLS — si se quiere HTTPS hay que agregar nginx como proxy.

- El fallback al pipeline LLM + full-text garantiza que la UI nunca 
  rompe aunque el VPS esté caído o en cold start.
