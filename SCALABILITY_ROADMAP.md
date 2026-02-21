# Scalability Roadmap for RAG SaaS Application

## Current Architecture (Free Tier MVP)

```
┌─────────────────────────────────────────────────────────────┐
│                     Current Setup                            │
├─────────────────────────────────────────────────────────────┤
│  Frontend (React) ──► Nginx ──► FastAPI Backend             │
│                                        │                     │
│                                        ▼                     │
│                              ┌─────────────────┐            │
│                              │    SQLite       │            │
│                              │  (Single File)  │            │
│                              └─────────────────┘            │
│                                        │                     │
│                                        ▼                     │
│                              ┌─────────────────┐            │
│                              │  FAISS (Local)  │            │
│                              │  Per-Tenant     │            │
│                              └─────────────────┘            │
└─────────────────────────────────────────────────────────────┘

Capacity: ~100 users, ~1000 documents, ~10 concurrent requests
```

---

## Phase 1: Basic Production (10-100 Tenants)

**Trigger:** First paying customers, consistent traffic

### Changes Required

```yaml
# docker-compose.prod.yml additions
services:
  postgres:
    image: postgres:15-alpine
    # Replaces SQLite
    
  redis:
    image: redis:7-alpine
    # For caching and rate limiting
```

### Implementation Steps

1. **Database Migration: SQLite → PostgreSQL**
   ```python
   # Update DATABASE_URL
   DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/ragdb
   ```

2. **Add Redis Caching**
   ```python
   # app/core/cache.py
   import redis.asyncio as redis
   
   class CacheService:
       def __init__(self):
           self.redis = redis.from_url(settings.redis_url)
       
       async def get_embedding(self, text_hash: str) -> list | None:
           cached = await self.redis.get(f"emb:{text_hash}")
           return json.loads(cached) if cached else None
       
       async def set_embedding(self, text_hash: str, embedding: list):
           await self.redis.setex(
               f"emb:{text_hash}", 
               3600 * 24,  # 24 hours
               json.dumps(embedding)
           )
   ```

3. **Rate Limiting with Redis**
   ```python
   # Move from in-memory to Redis-backed rate limiting
   async def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
       current = await self.redis.incr(key)
       if current == 1:
           await self.redis.expire(key, window)
       return current <= limit
   ```

### Expected Capacity
- **Users:** Up to 500
- **Documents:** Up to 10,000
- **Concurrent Requests:** 50
- **Cost:** ~$50-100/month (managed DB + small VPS)

---

## Phase 2: Multi-Instance Backend (100-500 Tenants)

**Trigger:** Single backend instance hitting CPU limits

### Architecture

```
                    ┌─────────────────────┐
                    │   Load Balancer     │
                    │   (nginx/Traefik)   │
                    └──────────┬──────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │  Backend 1  │     │  Backend 2  │     │  Backend 3  │
    │  (FastAPI)  │     │  (FastAPI)  │     │  (FastAPI)  │
    └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
           │                   │                   │
           └───────────────────┼───────────────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │  PostgreSQL │     │    Redis    │     │   Shared    │
    │  (Primary)  │     │   Cluster   │     │   Storage   │
    └─────────────┘     └─────────────┘     └─────────────┘
```

### Implementation Steps

1. **Horizontal Backend Scaling**
   ```yaml
   # docker-compose.scale.yml
   services:
     backend:
       deploy:
         replicas: 3
   ```

2. **Shared FAISS Index Storage**
   ```python
   # Move from local disk to S3/MinIO
   class VectorService:
       def __init__(self):
           self.s3 = boto3.client('s3')
           self.bucket = settings.faiss_bucket
       
       async def load_index(self, tenant_id: str):
           # Check local cache first
           if tenant_id in self._cache:
               return self._cache[tenant_id]
           
           # Download from S3
           index_path = f"/tmp/faiss/{tenant_id}/index.faiss"
           self.s3.download_file(
               self.bucket,
               f"indexes/{tenant_id}/index.faiss",
               index_path
           )
           return faiss.read_index(index_path)
   ```

3. **Session Stickiness or Stateless Design**
   ```nginx
   # nginx.conf for load balancing
   upstream backend {
       least_conn;
       server backend1:8000;
       server backend2:8000;
       server backend3:8000;
   }
   ```

### Expected Capacity
- **Users:** Up to 2,000
- **Documents:** Up to 50,000
- **Concurrent Requests:** 200
- **Cost:** ~$200-500/month

---

## Phase 3: Managed Vector Database (500+ Tenants)

**Trigger:** FAISS synchronization becomes bottleneck

### Recommended Solutions

| Provider | Best For | Pricing |
|----------|----------|---------|
| **Pinecone** | Simplicity | $70/month starter |
| **Weaviate Cloud** | Feature-rich | Pay-per-use |
| **Qdrant Cloud** | Cost-effective | $25/month starter |
| **Supabase pgvector** | PostgreSQL users | Included with DB |

### Migration to Qdrant (Recommended)

```python
# app/services/vector_service_qdrant.py
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

class QdrantVectorService:
    def __init__(self):
        self.client = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key
        )
    
    async def create_tenant_collection(self, tenant_id: str):
        await self.client.create_collection(
            collection_name=f"tenant_{tenant_id}",
            vectors_config=VectorParams(
                size=1536,
                distance=Distance.COSINE
            )
        )
    
    async def add_vectors(
        self, 
        tenant_id: str, 
        chunk_ids: list[str], 
        embeddings: list[list[float]]
    ):
        points = [
            PointStruct(id=idx, vector=emb, payload={"chunk_id": cid})
            for idx, (cid, emb) in enumerate(zip(chunk_ids, embeddings))
        ]
        await self.client.upsert(
            collection_name=f"tenant_{tenant_id}",
            points=points
        )
    
    async def search(
        self, 
        tenant_id: str, 
        query_vector: list[float], 
        top_k: int = 4
    ):
        results = await self.client.search(
            collection_name=f"tenant_{tenant_id}",
            query_vector=query_vector,
            limit=top_k
        )
        return [(r.payload["chunk_id"], r.score) for r in results]
```

### Architecture Update

```
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│  ┌─────────────┐        ┌─────────────┐                      │
│  │  Backend    │◄──────►│   Qdrant    │                      │
│  │  Cluster    │        │   Cloud     │                      │
│  └──────┬──────┘        └─────────────┘                      │
│         │                                                     │
│         ▼                                                     │
│  ┌─────────────┐        ┌─────────────┐                      │
│  │  PostgreSQL │◄──────►│  Read       │                      │
│  │  Primary    │        │  Replicas   │                      │
│  └─────────────┘        └─────────────┘                      │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

### Expected Capacity
- **Users:** Up to 10,000
- **Documents:** Up to 500,000
- **Concurrent Requests:** 1,000
- **Cost:** ~$500-1,500/month

---

## Phase 4: Enterprise Scale (1000+ Tenants)

**Trigger:** Global user base, strict SLAs needed

### Architecture Components

1. **Multi-Region Deployment**
   ```
   US-East ◄──────► US-West ◄──────► EU-West ◄──────► Asia-Pac
      │                │                │                │
      └────────────────┴────────────────┴────────────────┘
                            │
                    Global Load Balancer
                    (Cloudflare/AWS Global Accelerator)
   ```

2. **Database Sharding Strategy**
   ```python
   # Shard by tenant_id hash
   def get_shard(tenant_id: str, num_shards: int = 4) -> int:
       return int(hashlib.md5(tenant_id.encode()).hexdigest(), 16) % num_shards
   
   # Route queries to appropriate shard
   SHARDS = {
       0: "postgresql://shard0.db.example.com/ragdb",
       1: "postgresql://shard1.db.example.com/ragdb",
       2: "postgresql://shard2.db.example.com/ragdb",
       3: "postgresql://shard3.db.example.com/ragdb",
   }
   ```

3. **Event-Driven Processing**
   ```python
   # Use message queue for async document processing
   async def upload_document(file: UploadFile):
       # Save file to S3
       file_key = f"uploads/{tenant_id}/{uuid4()}.pdf"
       await s3.upload_fileobj(file.file, bucket, file_key)
       
       # Queue processing job
       await message_queue.publish(
           "document_processing",
           {
               "tenant_id": tenant_id,
               "file_key": file_key,
               "document_id": document.id
           }
       )
       
       return {"status": "processing", "document_id": document.id}
   ```

4. **Kubernetes Deployment**
   ```yaml
   # k8s/backend-deployment.yaml
   apiVersion: apps/v1
   kind: Deployment
   metadata:
     name: rag-backend
   spec:
     replicas: 5
     selector:
       matchLabels:
         app: rag-backend
     template:
       spec:
         containers:
         - name: backend
           image: rag-backend:latest
           resources:
             requests:
               memory: "512Mi"
               cpu: "250m"
             limits:
               memory: "2Gi"
               cpu: "1000m"
           livenessProbe:
             httpGet:
               path: /health
               port: 8000
           readinessProbe:
             httpGet:
               path: /health
               port: 8000
   ---
   apiVersion: autoscaling/v2
   kind: HorizontalPodAutoscaler
   metadata:
     name: rag-backend-hpa
   spec:
     scaleTargetRef:
       apiVersion: apps/v1
       kind: Deployment
       name: rag-backend
     minReplicas: 3
     maxReplicas: 20
     metrics:
     - type: Resource
       resource:
         name: cpu
         target:
           type: Utilization
           averageUtilization: 70
   ```

### Expected Capacity
- **Users:** 100,000+
- **Documents:** Millions
- **Concurrent Requests:** 10,000+
- **Cost:** $5,000-20,000/month

---

## Performance Optimization Checklist

### Query Optimization

```python
# 1. Add database indexes
class Document(Base):
    __table_args__ = (
        Index('idx_doc_tenant_status', 'tenant_id', 'status'),
        Index('idx_doc_created', 'created_at'),
    )

# 2. Batch embedding requests
async def get_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Batch up to 100 texts per API call"""
    batches = [texts[i:i+100] for i in range(0, len(texts), 100)]
    results = []
    for batch in batches:
        response = await openai.embeddings.create(
            model="text-embedding-3-small",
            input=batch
        )
        results.extend([e.embedding for e in response.data])
    return results

# 3. Connection pooling
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)
```

### Caching Strategy

```python
# Cache hierarchy
CACHE_LAYERS = {
    "L1": "In-Memory (LRU)",      # 100ms TTL, hot data
    "L2": "Redis",                 # 1 hour TTL, embeddings
    "L3": "S3/CDN",               # 24 hour TTL, static assets
}

# Embedding cache implementation
@cached(ttl=3600, key_builder=lambda t: f"emb:{hash(t)}")
async def get_embedding(text: str) -> list[float]:
    return await openai_client.get_embedding(text)
```

### Monitoring & Alerting

```python
# Add Prometheus metrics
from prometheus_client import Counter, Histogram

request_count = Counter(
    'rag_requests_total',
    'Total requests',
    ['endpoint', 'status']
)

request_latency = Histogram(
    'rag_request_latency_seconds',
    'Request latency',
    ['endpoint']
)

# Alert rules (prometheus.rules.yml)
groups:
- name: rag-alerts
  rules:
  - alert: HighErrorRate
    expr: rate(rag_requests_total{status="5xx"}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: High error rate detected
```

---

## Cost Optimization Tips

| Stage | Optimization | Savings |
|-------|--------------|---------|
| MVP | Use SQLite, local FAISS | ~$0/month |
| Phase 1 | Managed DB smallest tier | ~$30-50/month saved |
| Phase 2 | Reserved instances | 30-40% savings |
| Phase 3 | Spot instances for workers | 60-70% savings |
| Phase 4 | Negotiate enterprise pricing | Volume discounts |

### Embedding Cost Reduction

```python
# 1. Cache frequently asked questions
# 2. Use shorter text chunks when possible
# 3. Batch requests to reduce API calls
# 4. Consider local embedding models for cost-sensitive use cases

# Local embedding alternative (for Phase 3+)
from sentence_transformers import SentenceTransformer

class LocalEmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')  # Free!
    
    def get_embedding(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()
```

---

## Migration Checklist

### Before Each Phase

- [ ] Backup all data
- [ ] Test migration scripts on staging
- [ ] Plan maintenance window
- [ ] Prepare rollback procedure
- [ ] Update monitoring dashboards
- [ ] Notify users of downtime

### Phase Transition Triggers

| Metric | Phase 1 | Phase 2 | Phase 3 | Phase 4 |
|--------|---------|---------|---------|---------|
| Avg Response Time | >500ms | >300ms | >200ms | >100ms |
| CPU Utilization | >80% | >70% | >60% | >50% |
| Memory Usage | >80% | >70% | >60% | >50% |
| Error Rate | >1% | >0.5% | >0.1% | >0.01% |
| User Complaints | Rising | Any | Any | Any |

---

*Document Version: 1.0*
*Last Updated: [DATE]*
