from fastapi import FastAPI

from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para gerenciamento de chamados de suporte técnico.",
    debug=settings.debug,
)

app.include_router(auth_router)
app.include_router(users_router)


@app.get("/")
def read_root():
    return {
        "message": f"{settings.app_name} is running",
        "version": settings.app_version,
    }
