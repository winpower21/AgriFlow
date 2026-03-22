"""
Authentication router — token issuance via OAuth2 password flow.

Endpoints
---------
POST /auth/login
    Accepts OAuth2-compatible form data (``username`` + ``password``).
    Despite the field name ``username``, the value must be the user's
    **email address** (the User model has no ``username`` column).

    Returns a JWT bearer token together with basic user info (id, email,
    full_name, roles).

Authentication / authorisation
------------------------------
- This router has **no** auth dependency — it is the entry point for
  obtaining a token.
- The JWT payload stores ``{"user": <user.id>}`` and is signed with HS256.

Response schema: ``TokenWithUser``
"""

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import create_access_token
from app.crud import UserService
from app.database import get_db
from app.schemas import TokenWithUser

# No authentication dependency — this router issues tokens to unauthenticated callers.
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenWithUser)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    # OAuth2PasswordRequestForm has 'username' field, but we use email for authentication.
    # The client must send the user's email in the ``username`` form field.
    user_service = UserService(db)
    user, error = user_service.authenticate_user(form_data.username, form_data.password)
    if error == "invalid_credentials":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if error == "not_verified":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account has not been verified yet. Please contact an administrator.",
        )
    if error == "not_active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not active. Please contact an administrator.",
        )

    # Build a JWT whose payload is {"user": <int>} with a configurable expiry
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user": user.id}, expires_delta=access_token_expires
    )

    print(user.roles)  # Debug log — TODO: remove or replace with proper logging

    # Response includes the token plus a lightweight user summary so the
    # frontend can populate its auth store without an extra /me request.
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": [role.name for role in user.roles],
        },
    }
