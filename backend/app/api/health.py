from fastapi import APIRouter

from backend.app.embeddings import store

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict:
    try:
        vec_count = store.count()
    except Exception:  # noqa: BLE001
        vec_count = -1
    return {"status": "ok", "vectors": vec_count}
