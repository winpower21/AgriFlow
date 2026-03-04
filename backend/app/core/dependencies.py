from typing import Annotated, List

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.config import settings
from app.crud import UserService

# from app.crud.user import get_user, get_user_roles
from app.database import get_db
from app.models import User

# OAuth2 scheme defines where the client should get the token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the JWT token and retrieve the current user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        print(f"DEBUG get_current_user: token received = {token[:20]}...")
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        print(f"DEBUG get_current_user: payload = {payload}")
        id: str = payload.get("user")
        if id is None:
            print("DEBUG get_current_user: FAIL - 'user' key not in payload")
            raise credentials_exception
    except JWTError as e:
        print(f"DEBUG get_current_user: FAIL - JWTError: {e}")
        raise credentials_exception

    user_service = UserService(db)
    user = user_service.get_user(user_id=int(id))
    # user = get_user(db, user_id=int(id))
    if user is None:
        print(f"DEBUG get_current_user: FAIL - no user found for id={id}")
        raise credentials_exception
    print(f"DEBUG get_current_user: SUCCESS - user={user.email}")
    return user


def roles_required(required_role: str):
    """
    Dependency factory to check if user has a specific role.
    User must have exactly this role to access the route.

    Usage: user = Depends(roles_required("admin"))
    """

    def role_checker(
        user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> User:
        user_service = UserService(db)
        user_roles = user_service.get_user_roles(user_or_id=user)

        if required_role not in user_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User must have '{required_role}' role to access this resource",
            )

        return user

    return role_checker


def roles_accepted(accepted_roles: List[str]):
    """
    Dependency factory to check if user has any of the accepted roles.
    User must have at least one of the specified roles to access the route.

    Usage: user = Depends(roles_accepted(["admin", "manager"]))
    """

    def role_checker(
        user: User = Depends(get_current_user), db: Session = Depends(get_db)
    ) -> User:
        user_service = UserService(db)
        user_roles = user_service.get_user_roles(user_or_id=user)

        if not any(role in user_roles for role in accepted_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User must have one of these roles: {', '.join(accepted_roles)}",
            )

        return user

    return role_checker
