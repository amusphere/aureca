from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session
from svix.webhooks import Webhook, WebhookVerificationError

from app.config.auth import ClerkConfig
from app.database import get_session
from app.repositories.user import delete_user, get_user_br_column

router = APIRouter(prefix="/webhooks")

CLERK_WEBHOOK_SECRET = ClerkConfig.WEBHOOK_SECRET


@router.post("/clerk")
async def clerk_webhook(
    request: Request,
    session: Session = Depends(get_session),
):
    if not CLERK_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    payload: bytes = await request.body()
    headers = request.headers

    try:
        wh = Webhook(CLERK_WEBHOOK_SECRET)
        event = wh.verify(payload, headers)
    except WebhookVerificationError:
        raise HTTPException(status_code=400, detail="Invalid or outdated signature") from None

    if event["type"] == "user.deleted":
        clerk_user_id = event["data"]["id"]
        if clerk_user_id and (user := get_user_br_column(session, clerk_user_id, "clerk_sub")):
            delete_user(session, user)
    return {"received": True}
