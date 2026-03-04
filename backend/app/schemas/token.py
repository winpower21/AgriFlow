from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    """Schema for JWT token response."""

    access_token: str
    token_type: str


class TokenWithUser(Token):
    """Schema for JWT token response including user info."""

    user: dict

class TokenData(BaseModel):
    """Schema for data embedded in token."""

    user_id: Optional[int] = None
