from fastapi import FastAPI

from config import settings
from routers import users, events

app = FastAPI(title=settings.app_name)

app.include_router(users.router)
app.include_router(events.router)
