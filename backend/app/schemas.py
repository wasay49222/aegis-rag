from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from uuid import UUID

# --- Schemas for User Registration & Login ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

# --- Schema for the JWT Token ---
class Token(BaseModel):
    access_token: str
    token_type: str

# --- Schema for returning User Data ---
class UserResponse(BaseModel):
    id: UUID  # Changed from str to UUID to match the database
    email: str
    role: str

    # Updated to Pydantic V2 syntax (fixes the yellow warning)
    model_config = ConfigDict(from_attributes=True)