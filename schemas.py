import uuid
from datetime import datetime

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
