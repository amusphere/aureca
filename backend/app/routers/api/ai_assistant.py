from app.database import get_session
from app.models.ai_assistant import AIRequestModel, AIResponseModel
from app.schema import User
from app.services.ai import AIHub
from app.services.auth import auth_user
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

router = APIRouter(prefix="/ai", tags=["AI Assistant"])


@router.post("/process", response_model=AIResponseModel)
async def process_ai_request_endpoint(
    request: AIRequestModel,
    session: Session = Depends(get_session),
    user: User = Depends(auth_user),
):
    """AIアシスタントにリクエストを送信して処理結果を取得"""
    try:
        hub = AIHub(user.id, session)
        result = await hub.process_request(
            prompt=request.prompt, current_user=user
        )

        return AIResponseModel(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process AI request: {str(e)}",
        )
