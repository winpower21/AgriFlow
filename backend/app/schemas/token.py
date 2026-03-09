"""
Authentication / JWT token Pydantic schemas.

Defines the response models returned by the login endpoint as well as the
internal representation of data extracted from a decoded JWT.
"""

from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    """Response body returned after a successful login or token refresh.

    Fields:
        access_token: The signed JWT string.
        token_type:   The authorisation scheme, typically ``"bearer"``.
    """

    access_token: str
    token_type: str


class TokenWithUser(Token):
    """Extended token response that also includes basic user information.

    Returned by the login endpoint so the frontend can immediately populate
    the user profile without a separate ``/me`` request.

    Fields:
        user: Dictionary containing user details (id, email, roles, etc.).
    """

    user: dict


class TokenData(BaseModel):
    """Internal schema representing the payload decoded from a JWT.

    Used by the ``get_current_user`` dependency to identify the caller.

    Fields:
        user_id: The primary-key id of the authenticated user, extracted
                 from the JWT ``sub`` or custom claim.
    """

    user_id: Optional[int] = None
