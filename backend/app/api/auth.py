from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi.security import OAuth2PasswordBearer
from app.core.security import decode_token

from app.database import SessionLocal
from app.models import User
from app.schemas import UserCreate, UserLogin, Token, UserResponse
from app.core.security import hash_password, verify_password, create_access_token
from app.database import get_db

# Create the router (this groups our auth endpoints together)
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Helper to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # 1. Check if user already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 2. Hash the password and create the user
    hashed_pw = hash_password(user.password)
    new_user = User(email=user.email, hashed_password=hashed_pw, role="user")
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

@router.post("/login", response_model=Token)
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    # 1. Find the user
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    # 2. Verify the password
    if not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    # 3. Create the JWT token
    access_token = create_access_token(
        data={"sub": str(db_user.id), "role": db_user.role}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# This tells FastAPI where to look for the JWT token in the request headers
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    """
    The Security Guard: Extracts the JWT, verifies it, and returns the user.
    """
    # 1. Decode the token
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Extract the user ID from the token
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    # 3. Find the user in the database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
        
    return user

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Returns the current user's profile.
    This endpoint is PROTECTED. It requires a valid JWT.
    """
    return current_user

def require_admin(current_user: User = Depends(get_current_user)):
    """
    The Admin Bouncer: Checks if the logged-in user is an admin.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user