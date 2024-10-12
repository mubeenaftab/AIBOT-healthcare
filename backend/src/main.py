import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from src.api.endpoints import router as api_endpoint_routers
from src.config.settings.base import config_env
from src.config.settings.logger_config import logger
from src.repository.database import Base, engine
from src.scheduler.reminder_tasks import start_scheduler


def initialize_backend_application() -> FastAPI:
    app = FastAPI()
    Instrumentator().instrument(app).expose(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://healthcareaibot.netlify.app"],
        allow_credentials=config_env.IS_ALLOWED_CREDENTIALS,
        allow_methods=config_env.ALLOWED_METHODS,
        allow_headers=config_env.ALLOWED_HEADERS,
    )

    app.include_router(router=api_endpoint_routers)

    @app.on_event("startup")
    async def startup_event():
        """
        Function for application startup log and database initialization
        """
        logger.info("Application startup")
        await create_tables()
        start_scheduler()

    @app.on_event("shutdown")
    async def shutdown_event():
        """
        Function for application shutdown log
        """
        logger.info("Application shutdown")

    return app


backend_app: FastAPI = initialize_backend_application()


# Function to create the database tables
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    uvicorn.run(
        app="main:backend_app",
        host="0.0.0.0",
        reload=True,
    )
