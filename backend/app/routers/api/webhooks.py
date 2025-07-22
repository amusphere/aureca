import hashlib
import hmac
import json
import os
from typing import Any, Dict

from app.database import get_session
from app.repositories.user import delete_user, get_user_br_column
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

router = APIRouter(prefix="/webhooks")

CLERK_WEBHOOK_SECRET = os.getenv("CLERK_WEBHOOK_SECRET")


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """Verify Clerk webhook signature"""
    if not signature.startswith("v1,"):
        return False

    # Extract timestamp and signature
    parts = signature[3:].split(",")
    timestamp = None
    signatures = []

    for part in parts:
        if part.startswith("t="):
            timestamp = part[2:]
        elif part.startswith("v1="):
            signatures.append(part[3:])

    if not timestamp or not signatures:
        return False

    # Create expected signature
    signed_payload = f"{timestamp}.{payload.decode()}"
    expected_signature = hmac.new(
        secret.encode(), signed_payload.encode(), hashlib.sha256
    ).hexdigest()

    # Compare signatures
    return any(hmac.compare_digest(expected_signature, sig) for sig in signatures)


@router.post("/clerk")
async def clerk_webhook(request: Request, session: Session = Depends(get_session)):
    """Handle Clerk webhooks"""
    if not CLERK_WEBHOOK_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook secret not configured",
        )

    # Get signature from headers
    signature = request.headers.get("svix-signature")
    if not signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Missing signature header"
        )

    # Get payload
    payload = await request.body()

    # Verify signature
    if not verify_webhook_signature(payload, signature, CLERK_WEBHOOK_SECRET):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature"
        )

    try:
        # Parse JSON payload
        event_data: Dict[str, Any] = json.loads(payload.decode())
        event_type = event_data.get("type")

        if event_type == "user.deleted":
            # Extract Clerk user ID
            clerk_user_id = event_data.get("data", {}).get("id")

            if not clerk_user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Missing user ID in webhook data",
                )

            # Find user in database by clerk_sub
            user = get_user_br_column(session, clerk_user_id, "clerk_sub")

            if user:
                # Delete user from database (cascade delete will handle related data)
                delete_user(session, user)
                print(f"Successfully deleted user {clerk_user_id} from database")
            else:
                print(f"User {clerk_user_id} not found in database")

        return {"received": True}

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload"
        )
    except Exception as e:
        print(f"Error processing webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing webhook",
        )
