from fastapi import FastAPI

from config import settings
from routers import auth, users, events

app = FastAPI(title=settings.app_name)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)
