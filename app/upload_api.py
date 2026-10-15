"""Authenticated bounded multipart uploads and owner-bound result delivery."""

import hashlib
from typing import Any

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from core.audit import get_audit_logger
from core.config import get_config
from core.security import authenticate, is_authorized
from core.upload_gate import UploadRejected
from core.uploads import UploadService

router = APIRouter()
_SERVICE: UploadService | None = None


def set_upload_service(service: UploadService | None) -> None:
    global _SERVICE
    _SERVICE = service


def upload_service() -> UploadService:
    if _SERVICE is None:
        raise HTTPException(status_code=503, detail="Upload service is not initialized")
    return _SERVICE


def owner_for(api_key: str | None) -> str:
    role, _ = authenticate(api_key)
    if api_key not in get_config().api_keys or not is_authorized(role, "upload:create"):
        get_audit_logger().log_security("upload_access_denied", role, "Upload permission required")
        raise HTTPException(status_code=403, detail="Upload permission required")
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


class UploadBodyLimit:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] != "/uploads" or scope["method"] != "POST":
            await self.app(scope, receive, send)
            return
        limit = int(get_config().get("uploads.max_request_bytes"))
        data = bytearray()
        headers = dict(scope["headers"])
        try:
            declared = int(headers.get(b"content-length", b"0"))
        except ValueError:
            declared = limit + 1
        if declared > limit:
            await self._reject(scope, receive, send)
            return
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            data.extend(message.get("body", b""))
            if len(data) > limit:
                await self._reject(scope, receive, send)
                return
            if not message.get("more_body", False):
                break
        delivered = False
        async def bounded_receive() -> Message:
            nonlocal delivered
            if delivered:
                return await receive()
            delivered = True
            return {"type": "http.request", "body": bytes(data), "more_body": False}
        await self.app(scope, bounded_receive, send)

    @staticmethod
    async def _reject(scope: Scope, receive: Receive, send: Send) -> None:
        get_audit_logger().log_security("upload_rejected", "caller", "Request exceeds upload body limit", reason="request_size")
        await JSONResponse({"detail": "Upload request too large"}, status_code=413)(scope, receive, send)


@router.post("/uploads")
def submit_upload(file: UploadFile = File(...), customer_message: str = Form(""),
                  purpose: str = Form("invoice"), language: str = Form("en"),
                  x_api_key: str | None = Header(default=None)) -> JSONResponse:
    owner = owner_for(x_api_key)
    service = upload_service()
    try:
        data = file.file.read(int(get_config().get("uploads.max_bytes")) + 1)
        result = service.submit(data, file.filename or "", file.content_type or "", owner, customer_message, purpose, language)
    except UploadRejected as exc:
        raise HTTPException(status_code=422, detail=exc.reason) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Invalid upload parameters") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Upload queue unavailable") from exc
    finally:
        file.file.close()
    return JSONResponse(result, status_code=202 if result["background"] else 200)


@router.get("/uploads/{job_id}")
def upload_result(job_id: str, x_api_key: str | None = Header(default=None)) -> dict[str, Any]:
    owner = owner_for(x_api_key)
    try:
        return upload_service().get(job_id, owner)
    except (ValueError, PermissionError) as exc:
        get_audit_logger().log_security("upload_result_denied", "caller", "Unknown or foreign upload")
        raise HTTPException(status_code=404, detail="Upload not found") from exc
