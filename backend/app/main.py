from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import health, policies, tasks, packages, reviews # NAYA: reviews import kiya


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Enterprise Agentic Coordination & Intelligence Platform",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(tasks.router)
    app.include_router(policies.router)
    app.include_router(packages.router)
    app.include_router(reviews.router) # NAYA ROUTER

    @app.get("/")
    async def root():
        return {"message": "EACIP API", "docs": "/docs"}

    return app


app = create_app()
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import health, policies, tasks, packages, reviews
# NAYA IMPORT
from app.services.checkpointer import get_langgraph_checkpointer, close_checkpointer

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup event
    await get_langgraph_checkpointer()
    yield
    # Shutdown event
    await close_checkpointer()

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Enterprise Agentic Coordination & Intelligence Platform",
        lifespan=lifespan,  # NAYA: Lifespan add kiya
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(tasks.router)
    app.include_router(policies.router)
    app.include_router(packages.router)
    app.include_router(reviews.router)

    @app.get("/")
    async def root():
        return {"message": "EACIP API", "docs": "/docs"}

    return app

app = create_app()