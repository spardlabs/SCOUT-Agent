import hashlib
import hmac

from fastapi import APIRouter, HTTPException, Query, Request

from scout.config import settings
from scout.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/dropbox")
async def dropbox_webhook_verify(challenge: str = Query(...)):
    """Dropbox webhook verification endpoint. Returns the challenge parameter."""
    return {"challenge": challenge}


@router.post("/dropbox")
async def dropbox_webhook_receive(request: Request):
    """Receive Dropbox file change notifications."""
    body = await request.body()

    # Verify signature
    signature = request.headers.get("X-Dropbox-Signature", "")
    if settings.dropbox_webhook_secret:
        expected = hmac.new(
            settings.dropbox_webhook_secret.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise HTTPException(status_code=403, detail="Invalid signature")

    data = await request.json()
    accounts = data.get("list_folder", {}).get("accounts", [])

    logger.info("dropbox_webhook_received", account_count=len(accounts))

    # Enqueue ingest tasks for each account
    from scout.tasks.ingest import process_dropbox_changes

    for account_id in accounts:
        process_dropbox_changes.delay(account_id)

    return {"status": "ok"}


@router.post("/google-drive")
async def google_drive_webhook_receive(request: Request):
    """Receive Google Drive push notification for file changes."""
    channel_id = request.headers.get("X-Goog-Channel-ID", "")
    resource_state = request.headers.get("X-Goog-Resource-State", "")

    if resource_state == "sync":
        # Initial sync notification, acknowledge
        return {"status": "ok"}

    logger.info(
        "google_drive_webhook_received",
        channel_id=channel_id,
        resource_state=resource_state,
    )

    from scout.tasks.ingest import process_google_drive_changes

    process_google_drive_changes.delay(channel_id)

    return {"status": "ok"}
