from fastapi import FastAPI

from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para gerenciamento de chamados de suporte técnico.",
    debug=settings.debug,
)


@app.get("/")
def read_root():
    return {
        "message": f"{settings.app_name} is running",
        "version": settings.app_version,
    }
