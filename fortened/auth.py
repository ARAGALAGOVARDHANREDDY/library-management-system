import os
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from jose import JWTError, jwt
from passlib.context import CryptContext

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status
)
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import models
import schemas

from database import get_db


load_dotenv()

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30)
)

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is missing from .env file")


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login",
    auto_error=False
)


# -------------------------------
# PASSWORD FUNCTIONS
# -------------------------------

def hash_password(password: str):
    if len(password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password must not exceed 72 bytes."
        )

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    if len(plain_password.encode("utf-8")) > 72:
        return False

    return pwd_context.verify(
        plain_password,
        hashed_password
    )


# -------------------------------
# JWT TOKEN
# -------------------------------

def create_access_token(data: dict):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# -------------------------------
# GET LOGGED-IN USER
# -------------------------------

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Please log in first to borrow a book.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token."
            )

        user_id = int(user_id)

    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user = db.query(models.User).filter(
        models.User.id == user_id
    ).first()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User account not found."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Your account is inactive. Contact the librarian."
        )

    return user


# -------------------------------
# ROLE-BASED ACCESS
# -------------------------------

def require_roles(*allowed_roles):

    def role_checker(
        current_user: models.User = Depends(get_current_user)
    ):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to access this resource."
            )

        return current_user

    return role_checker


# -------------------------------
# REGISTER
# -------------------------------

@router.post(
    "/register",
    response_model=schemas.UserResponse
)
def register_user(
    request: schemas.UserRegister,
    db: Session = Depends(get_db)
):

    # Only students can register through this endpoint.
    if request.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Only student registration is allowed."
        )

    # Check whether email already has an account.
    existing_user = db.query(models.User).filter(
        models.User.email == request.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered. Please log in."
        )

    # Check whether Member ID exists.
    member = db.query(models.Member).filter(
        models.Member.id == request.member_id
    ).first()

    if not member:
        raise HTTPException(
            status_code=404,
            detail="Member ID not found. Contact the librarian."
        )

    # Verify that the email belongs to this member.
    if member.email.lower() != request.email.lower():
        raise HTTPException(
            status_code=400,
            detail="Email does not match the registered Member ID."
        )

    # Check whether this member already has an account.
    existing_member_user = db.query(models.User).filter(
        models.User.member_id == member.id
    ).first()

    if existing_member_user:
        raise HTTPException(
            status_code=400,
            detail="This member already has a login account."
        )

    # Create student account.
    new_user = models.User(
        email=request.email,
        password_hash=hash_password(request.password),
        role="student",
        member_id=member.id,
        is_active=True
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Registration failed. Please try again."
        )

    return new_user


# -------------------------------
# LOGIN
# -------------------------------

@router.post(
    "/login",
    response_model=schemas.TokenResponse
)
def login_user(
    request: schemas.LoginRequest,
    db: Session = Depends(get_db)
):

    user = db.query(models.User).filter(
        models.User.email == request.email
    ).first()

    if not user or not verify_password(
        request.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Your account is inactive. Contact the librarian."
        )

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# -------------------------------
# CURRENT USER
# -------------------------------

@router.get(
    "/me",
    response_model=schemas.UserResponse
)
def get_my_account(
    current_user: models.User = Depends(get_current_user)
):
    return current_user
@router.post(
    "/admin/create-user",
    response_model=schemas.UserResponse,
    status_code=201
)
def create_staff_user(
    request: schemas.StaffUserCreate,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(require_roles("admin"))
):

    # Normalize email
    email = str(request.email).strip().lower()

    # Check duplicate email
    existing_user = (
        db.query(models.User)
        .filter(models.User.email == email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists."
        )

    # Check bcrypt password limit
    if len(request.password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=400,
            detail="Password must not exceed 72 bytes."
        )

    # Create staff account
    new_user = models.User(
        email=email,
        password_hash=hash_password(request.password),
        role=request.role,
        member_id=None,
        is_active=True
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    except Exception:
        db.rollback()
        raise