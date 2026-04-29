from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.ai.errors import LLMProviderError
from app.core.config import settings
from app.core.setup import ensure_local_runtime
from app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    _ = app
    ensure_local_runtime()
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.client_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)
    app.include_router(api_router, prefix="/api")

    @app.exception_handler(LLMProviderError)
    async def llm_provider_exception_handler(request, exc: LLMProviderError):
        _ = request
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    return app


app = create_app()
