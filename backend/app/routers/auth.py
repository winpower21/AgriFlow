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

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenWithUser)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db),
):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    # OAuth2PasswordRequestForm has 'username' field, but we use email for authentication. The email has to be sent as 'username' in the form data.
    user_service = UserService(db)
    user = user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"user": user.id}, expires_delta=access_token_expires
    )

    print(user.roles)

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
