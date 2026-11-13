# Architecture

This document describes the high-level architecture of the **AI Developer Trends Intelligence Platform**.

## Layers

1. **Scraping** (`backend/app/scraping/`)
   Async HTTP clients with retries + rate limiting, plus an optional Scrapy spider.
   Sources: Reddit JSON, Hacker News Firebase API, GitHub Trending HTML, arXiv Atom.

2. **ETL** (`backend/app/pipelines/etl.py`)
   Normalizes scraped items into the `Document` schema, deduplicates by SHA-256 of
   `(source, external_id, title, body)`.

3. **Embeddings** (`backend/app/embeddings/`)
   Local `sentence-transformers/all-MiniLM-L6-v2` model (384-dim, cosine).
   Vectors stored in a persistent ChromaDB collection.

4. **Trends** (`backend/app/pipelines/trends.py`)
   Daily term-frequency buckets, with deltas vs the previous bucket.

5. **Topics** (`backend/app/pipelines/topics.py`)
   k-means clustering over recent embeddings; topics are labelled with their most distinctive terms (TF-IDF across clusters).

6. **AI summaries** (`backend/app/ai/ollama.py`)
   Async client against a locally running Ollama daemon (`llama3` by default).

7. **API** (`backend/app/api/`)
   FastAPI routers: `/health`, `/sources`, `/search`, `/trends`, `/topics`, `/summary`.

8. **Frontend** (`frontend/`)
   React + Vite + Tailwind. Pages: Overview, Search, Trends, Topics, Sources.

## Data Flow

```
scrape -> ingest_items (dedup) -> embed_pending -> Chroma
                                     |
                                     +-> compute_daily_trends
                                     +-> cluster_topics
```

## Storage

- **PostgreSQL** (docker-compose default) or **SQLite** (local fallback) for structured data.
- **ChromaDB** persistent store under `./data/chroma` for vectors.
