from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import DbDep
from app.schemas.auth import Token, UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.utils.exceptions import AuthenticationError, UserAlreadyExistsError

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(data: UserCreate, db: DbDep) -> UserResponse:
    """
    Create a new user with the provided email, username, and password.
    Returns the created user profile (password is never returned).
    """
    try:
        return AuthService.create_user(db, data)
    except UserAlreadyExistsError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post(
    "/login",
    response_model=Token,
    summary="Login and obtain a JWT access token",
)
def login(
    db: DbDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    Authenticate with username + password (form-encoded).
    Returns a Bearer token valid for the configured expiry window.
    """
    try:
        user = AuthService.authenticate(db, form_data.username, form_data.password)
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.message,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    token = AuthService.create_access_token(data={"sub": user.username})
    return Token(access_token=token)
