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
    # Pola dostępne wyłącznie dla moderatora (walidacja w routerze)
    status: str | None = Field(default=None, min_length=1)
    blacklisted: bool | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class EventStatus(str, Enum):
    szkic = "szkic"
    oczekujace_na_akceptacje = "oczekujace_na_akceptacje"
    zaakceptowane = "zaakceptowane"
    odrzucone = "odrzucone"


class EventCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str
    public: bool
    participant_limit: int
    social_media_links: str


class EventUpdate(BaseModel):
    # Tylko pola treści; status zmienia się wyłącznie przez akcje submit/approve/reject
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    public: bool | None = None
    participant_limit: int | None = None
    social_media_links: str | None = None


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


class LocationType(str, Enum):
    pwr = "pwr"
    wlasne = "wlasne"


class LocationCreate(BaseModel):
    name: str = Field(min_length=1, description="Nazwa potoczna, np. Sala Teatralna")
    address_id: uuid.UUID
    type: LocationType
    capacity: int | None = None
    is_active: bool = True

class LocationRead(BaseModel):
    id: uuid.UUID
    name: str
    address_id: uuid.UUID
    type: LocationType
    capacity: int | None
    is_active: bool


class EventBlacklistCreate(BaseModel):
    event_id: uuid.UUID
    user_id: uuid.UUID
    reason: str = Field(min_length=1)

class EventBlacklistRead(BaseModel):
    event_id: uuid.UUID
    user_id: uuid.UUID
    reason: str
