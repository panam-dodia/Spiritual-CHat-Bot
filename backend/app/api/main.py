# Replace your backend/app/api/main.py with this clean version
# This fixes the encoding issue

from fastapi import APIRouter

from app.api.routes import items, login, private, users, utils
from app.core.config import settings

# Import organizations route
try:
    from app.api.routes import organizations
    ORGANIZATIONS_AVAILABLE = True
    print("Organizations routes imported successfully")
except ImportError as e:
    print(f"Warning: Organizations routes not available: {e}")
    ORGANIZATIONS_AVAILABLE = False

api_router = APIRouter()

# Include existing routes
api_router.include_router(login.router)
api_router.include_router(users.router)
api_router.include_router(utils.router)
api_router.include_router(items.router)

# Include organizations route if available
if ORGANIZATIONS_AVAILABLE:
    api_router.include_router(organizations.router)
    print("Organizations routes included successfully")
else:
    print("Organizations routes not included - check organizations.py file")

# Include private routes for local environment
if settings.ENVIRONMENT == "local":
    api_router.include_router(private.router)