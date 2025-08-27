from fastapi import APIRouter
from app.api.v1.endpoints import user, reports, admin

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(user.router)
api_router.include_router(reports.router)
api_router.include_router(admin.router)
