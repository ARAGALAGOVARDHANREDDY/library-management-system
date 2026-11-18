
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from datetime import datetime
from typing import Optional, Literal


# -------------------------
# BOOK SCHEMAS
# -------------------------

class BookCreate(BaseModel):
    title: str
    author: str
    category: str
    total_copies: int = Field(ge=1)


class BookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    category: Optional[str] = None
    total_copies: Optional[int] = Field(default=None, ge=1)


class BookResponse(BaseModel):
    id: int
    title: str
    author: str
    category: str
    total_copies: int
    available_copies: int

    model_config = ConfigDict(from_attributes=True)


# -------------------------
# MEMBER SCHEMAS
# -------------------------

class MemberCreate(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None


class MemberUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None


class MemberResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# -------------------------
# BORROWING SCHEMAS
# -------------------------

class BorrowRequest(BaseModel):
    # Student only needs to send the book ID.
    # Member ID is obtained from the logged-in user.
    book_id: int = Field(gt=0)


class BorrowResponse(BaseModel):
    id: int
    book_id: int
    member_id: int
    borrowed_at: datetime
    returned_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# -------------------------
# AUTHENTICATION SCHEMAS
# -------------------------

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: str = "student"
    member_id: Optional[int] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    role: str
    member_id: Optional[int]
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class StaffUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    role: Literal["admin", "librarian"]
