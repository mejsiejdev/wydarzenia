from fastapi import FastAPI

from config import settings
from routers import auth, users, events, locations, event_blacklists

app = FastAPI(title=settings.app_name)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(locations.router)
app.include_router(event_blacklists.router)
