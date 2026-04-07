from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI

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

    # Include routers
    from scout.api.routes import users, profiles, jobs, clips, webhooks, social, analytics

    app.include_router(users.router, prefix="/api/users", tags=["users"])
    app.include_router(profiles.router, prefix="/api/profiles", tags=["profiles"])
    app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
    app.include_router(clips.router, prefix="/api/clips", tags=["clips"])
    app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
    app.include_router(social.router, prefix="/api/social", tags=["social"])
    app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])

    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "scout-agent"}

    return app


app = create_app()
