"""Customer-only static interface and non-sensitive client configuration."""

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

from core.config import get_config

router = APIRouter()
ROOT = Path(__file__).resolve().parent / "web"


@router.get("/", include_in_schema=False)
def customer_page() -> FileResponse:
    return FileResponse(ROOT / "index.html")


@router.get("/client-config", include_in_schema=False)
def client_configuration() -> dict:
    cfg = get_config()
    return {"languages": cfg.languages, "max_upload_bytes": cfg.get("uploads.max_bytes"),
            "upload_types": cfg.get("uploads.allowed_types")}
