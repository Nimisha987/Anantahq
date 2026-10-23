"""Application factory."""
from fastapi import FastAPI

from .api import register_error_handlers , router
from .config import Settings
from .database import init_db
from .service import Clock, utc_now

def create_app(settings:Settings | None = None, clock:Clock = utc_now)->FastAPI:
    settings = settings or Settings.from_env()
    init_db(settings.db_path)

    app = FastAPI(
        title="URL Shortener",
        version = "1.0.0",
        description = "Create short links, redirect to them and track clicks.",

    )
    app.state.settings = settings
    app.state.clock = clock
    register_error_handlers(app)
    app.include_router(router)
    return app