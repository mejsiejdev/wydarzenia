import uuid
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    # bcrypt restricts input to 72 chars
    password: str = Field(min_length=8, max_length=72)
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)


class UserRead(BaseModel):
    id: uuid.UUID
    email: EmailStr
    first_name: str
    last_name: str
    status: str
    blacklisted: bool
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)
    first_name: str | None = Field(default=None, min_length=1)
    last_name: str | None = Field(default=None, min_length=1)


class EventStatus(str, Enum):
    szkic = "szkic"
    oczukujace_na_akceptacje = "oczukujace_na_akceptacje"
    zaakceptowane = "zaakceptowane"
    odrzucone = "odrzucone"


class EventCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str
    public: bool
    status: EventStatus = EventStatus.szkic
    participant_limit: int
    social_media_links: str
    created_by: uuid.UUID


class EventRead(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    public: bool
    status: EventStatus
    participant_limit: int
    social_media_links: str
    created_at: datetime
    created_by: uuid.UUID
