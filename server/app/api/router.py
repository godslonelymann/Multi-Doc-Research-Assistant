from fastapi import APIRouter

from app.api.routes import chat, comparison, documents, health, reports, summaries, workspaces

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(comparison.router, tags=["comparison"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(summaries.router, prefix="/summaries", tags=["summaries"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
