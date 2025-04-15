from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, APIRouter, status
from loguru import logger

from app.auth.router import router as router_auth
from app.api.router import router as router_api
from app.pages.router import router as router_pages


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application initialization...")
    yield
    logger.info("Stopping application...")


def register_routers(app: FastAPI) -> None:
    """
    Registers routers for app
    """
    router_root = APIRouter()

    @router_root.get("/", tags=["root"])
    def home_page():
        return RedirectResponse("/posts",
                                status_code=status.HTTP_301_MOVED_PERMANENTLY)

    app.include_router(router_root, tags=["root"])
    app.include_router(router_auth)
    app.include_router(router_api)
    app.include_router(router_pages)


def init_app() -> FastAPI:
    """
    Creation and configuring FastAPI application
    Returns:
        Configured FastAPI app
    """
    app = FastAPI(lifespan=lifespan, docs_url="/api")

    # Allow backend communicate with JS from different origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    app.mount("/static",
              StaticFiles(directory="app/static"),
              name="static"
              )

    register_routers(app)
    return app


app = init_app()
