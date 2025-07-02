from app.database import get_session
from app.models.ai_assistant import AIRequestModel, AIResponseModel
from app.schema import User
from app.services.ai.orchestrator import AIOrchestrator
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
        orchestrator = AIOrchestrator(user.id, session)
        result = await orchestrator.process_request(request.prompt)

        return AIResponseModel(**result)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process AI request: {str(e)}",
        )
