from pydantic import BaseModel, ConfigDict
from typing import Generic, TypeVar, Optional

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    message: Optional[str] = None
    type: Optional[str] = None
    data: T


def success_response(data, message: str = None, type: str = "success"):
    return ApiResponse(data=data, message=message, type=type)
