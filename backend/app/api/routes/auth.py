from fastapi import APIRouter, HTTPException, status, Depends, Request
from app.models.user import UserCreate, UserLogin, UserResponse, TokenResponse
from app.db.repositories.user_repository import user_repository
from app.core import security

router = APIRouter()

@router.post("/register", response_model=TokenResponse)
async def register(user_in: UserCreate):
    hashed_password = security.hash_password(user_in.password)
    try:
        user_doc = await user_repository.create_user(user_in.email, hashed_password)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    user_id = str(user_doc["_id"])
    access_token = security.create_access_token(user_id=user_id, email=user_doc["email"])
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(id=user_id, email=user_doc["email"])
    )

@router.post("/login", response_model=TokenResponse)
async def login(user_in: UserLogin):
    user_doc = await user_repository.get_user_by_email(user_in.email)
    if not user_doc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    if not security.verify_password(user_in.password, user_doc["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    user_id = str(user_doc["_id"])
    access_token = security.create_access_token(user_id=user_id, email=user_doc["email"])
    
    return TokenResponse(
        access_token=access_token,
        user=UserResponse(id=user_id, email=user_doc["email"])
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user(request: Request):
    if not hasattr(request.state, "user"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    user_info = request.state.user
    return UserResponse(id=user_info["sub"], email=user_info["email"])
