import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.models.user import User
from app.schemas.auth import UserCreate
from app.utils.exceptions import AuthenticationError, UserAlreadyExistsError
from app.utils.security import get_password_hash, verify_password

logger = logging.getLogger(__name__)


class AuthService:
    """Handles user registration, login, and JWT token operations."""

    @staticmethod
    def create_user(db: Session, data: UserCreate) -> User:
        """Register a new user after checking for duplicates."""
        if db.query(User).filter(User.email == data.email).first():
            raise UserAlreadyExistsError("Email address is already registered")
        if db.query(User).filter(User.username == data.username).first():
            raise UserAlreadyExistsError("Username is already taken")

        user = User(
            id=str(uuid.uuid4()),
            email=data.email,
            username=data.username,
            hashed_password=get_password_hash(data.password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("Registered new user: %s (%s)", user.username, user.email)
        return user

    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> User:
        """Verify credentials and return the authenticated user."""
        user = db.query(User).filter(User.username == username).first()
        if not user or not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid username or password")
        if not user.is_active:
            raise AuthenticationError("Account is disabled")
        return user

    @staticmethod
    def create_access_token(
        data: dict, expires_delta: Optional[timedelta] = None
    ) -> str:
        """Encode a JWT access token with an expiry claim."""
        payload = data.copy()
        expire = datetime.now(timezone.utc) + (
            expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        payload["exp"] = expire
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def get_current_user(db: Session, token: str) -> User:
        """Decode a JWT and return the corresponding user."""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            username: Optional[str] = payload.get("sub")
            if not username:
                raise AuthenticationError("Token is missing subject claim")
        except JWTError as exc:
            raise AuthenticationError("Token is invalid or expired") from exc

        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise AuthenticationError("User not found")
        return user
