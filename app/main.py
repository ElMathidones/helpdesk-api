from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.categories import router as categories_router
from app.api.routes.comments import router as comments_router
from app.api.routes.tickets import router as tickets_router
from app.api.routes.users import router as users_router
from app.api.routes.websocket import router as websocket_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API para gerenciamento de chamados de suporte técnico.",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(users_router)
app.include_router(categories_router)
app.include_router(tickets_router)
app.include_router(comments_router)
app.include_router(websocket_router)


@app.get("/")
def read_root():
    return {
        "message": f"{settings.app_name} is running",
        "version": settings.app_version,
    }
