from fastapi import FastAPI

from config import settings
from routers import users

app = FastAPI(title=settings.app_name)

app.include_router(users.router)
