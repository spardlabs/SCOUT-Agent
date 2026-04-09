from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from scout.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="SCOUT-Agent",
        description="Agentic podcast post-production pipeline",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS - allow frontend to talk directly to backend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3001", "http://localhost:3002", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    from scout.api.routes import users, profiles, jobs, clips, webhooks, social, analytics, upload, media_files

    app.include_router(users.router, prefix="/api/users", tags=["users"])
    app.include_router(profiles.router, prefix="/api/profiles", tags=["profiles"])
    app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
    app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
    app.include_router(clips.router, prefix="/api/clips", tags=["clips"])
    app.include_router(media_files.router, prefix="/api/media", tags=["media"])
    app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
    app.include_router(social.router, prefix="/api/social", tags=["social"])
    app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "scout-agent"}

    return app


app = create_app()
