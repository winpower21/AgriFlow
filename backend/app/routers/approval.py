from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user, roles_required
from ..crud.approval import ApprovalService
from ..database import get_db
from ..models.user import User
from ..schemas.approval import (
    ApprovalItemAction,
    ApprovalRequestCreate,
    ApprovalRequestSchema,
)

router = APIRouter(
    prefix="/approvals",
    tags=["approvals"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


def _is_admin(user: User, db: Session) -> bool:
    from ..crud.user import UserService
    return "admin" in UserService(db).get_user_roles(user_or_id=user)


@router.get("/", response_model=list[ApprovalRequestSchema])
def get_approvals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_admin = _is_admin(current_user, db)
    return ApprovalService(db).get_all(user_id=current_user.id, is_admin=is_admin)


@router.post("/", response_model=ApprovalRequestSchema, status_code=201)
def submit_request(
    data: ApprovalRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApprovalService(db).create(user_id=current_user.id, data=data)


@router.patch("/{request_id}/items/{item_index}", response_model=ApprovalRequestSchema,
              dependencies=[Depends(roles_required("admin"))])
def act_on_item(
    request_id: int,
    item_index: int,
    action_data: ApprovalItemAction,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = ApprovalService(db).act_on_item(request_id, item_index, action_data, current_user.id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request or item not found")
    return result


@router.post("/{request_id}/approve-all", response_model=ApprovalRequestSchema,
             dependencies=[Depends(roles_required("admin"))])
def approve_all(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = ApprovalService(db).approve_all(request_id, current_user.id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return result


@router.post("/{request_id}/reject-all", response_model=ApprovalRequestSchema,
             dependencies=[Depends(roles_required("admin"))])
def reject_all(
    request_id: int,
    note: Optional[str] = Body(None, embed=True),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = ApprovalService(db).reject_all(request_id, current_user.id, note=note)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return result
