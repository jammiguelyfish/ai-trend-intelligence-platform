# API

Base URL (local): `http://localhost:8000`

Interactive docs: `http://localhost:8000/docs` (Swagger) and `/redoc`.

## Endpoints

### GET `/health`
```json
{ "status": "ok", "vectors": 1234 }
```

### GET `/sources`
List configured sources auto-created during ingestion.

### GET `/search?q=<text>&k=10`
Semantic search across all embedded documents.

### GET `/trends?bucket=YYYY-MM-DD&limit=50`
Top terms for a day bucket (omit `bucket` to get most-trending across all buckets).

### GET `/trends/buckets`
List available day buckets, newest first.

### GET `/topics`
List k-means topics with label, keywords, size, and the 3 most representative documents.

### POST `/summary`
```json
{ "document_id": 42 }
```
Returns an LLM-generated summary (via Ollama).
