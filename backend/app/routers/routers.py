from fastapi import APIRouter

from app.routers.api.admin import router as admin_router
from app.routers.api.ai_assistant import router as ai_assistant_router
from app.routers.api.chat import router as chat_router
from app.routers.api.google_oauth import router as google_oauth_router
from app.routers.api.health import router as health_router
from app.routers.api.mail import router as mail_router
from app.routers.api.tasks import router as tasks_router
from app.routers.api.users import router as users_router
from app.routers.api.webhooks import router as webhooks_router

api_router = APIRouter()

api_router.include_router(health_router, prefix="/api", tags=["Health"])
api_router.include_router(users_router, prefix="/api", tags=["Users"])
api_router.include_router(google_oauth_router, prefix="/api", tags=["Google OAuth"])
api_router.include_router(ai_assistant_router, prefix="/api", tags=["AI Assistant"])
api_router.include_router(chat_router, prefix="/api", tags=["Chat"])
api_router.include_router(tasks_router, prefix="/api", tags=["Tasks"])
api_router.include_router(mail_router, prefix="/api", tags=["Mail"])
api_router.include_router(webhooks_router, prefix="/api", tags=["Webhooks"])
api_router.include_router(admin_router, prefix="/api", tags=["Admin"])
