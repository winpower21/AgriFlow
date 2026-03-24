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
    ApprovalRequestUpdate,
)
from ..schemas.response import ApiResponse

router = APIRouter(
    prefix="/approvals",
    tags=["approvals"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)


def _is_admin(user: User, db: Session) -> bool:
    from ..crud.user import UserService
    return "admin" in UserService(db).get_user_roles(user_or_id=user)


@router.get("/", response_model=ApiResponse[list[ApprovalRequestSchema]])
def get_approvals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    is_admin = _is_admin(current_user, db)
    return ApiResponse(data=ApprovalService(db).get_all(user_id=current_user.id, is_admin=is_admin))


@router.post("/", response_model=ApiResponse[ApprovalRequestSchema], status_code=201)
def submit_request(
    data: ApprovalRequestCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ApiResponse(
        data=ApprovalService(db).create(user_id=current_user.id, data=data),
        message="Approval request submitted",
        type="success",
    )


@router.patch("/{request_id}/items/{item_index}", response_model=ApiResponse[ApprovalRequestSchema],
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
    return ApiResponse(data=result, message="Item updated", type="success")


@router.post("/{request_id}/approve-all", response_model=ApiResponse[ApprovalRequestSchema],
             dependencies=[Depends(roles_required("admin"))])
def approve_all(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    result = ApprovalService(db).approve_all(request_id, current_user.id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")
    return ApiResponse(data=result, message="All items approved", type="success")


@router.post("/{request_id}/reject-all", response_model=ApiResponse[ApprovalRequestSchema],
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
    return ApiResponse(data=result, message="All items rejected", type="success")


@router.put("/{request_id}", response_model=ApiResponse[ApprovalRequestSchema])
def update_approval(
    request_id: int,
    body: ApprovalRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = ApprovalService(db)
    try:
        result = svc.update(request_id, current_user.id, body)
    except ValueError as e:
        if str(e) == "not_owner":
            raise HTTPException(status_code=403, detail="You can only edit your own requests")
        if str(e) == "not_pending":
            raise HTTPException(status_code=409, detail="Only pending requests can be edited")
        raise
    if not result:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return ApiResponse(data=result, message="Approval request updated", type="success")


@router.delete("/{request_id}", response_model=ApiResponse[None])
def delete_approval(
    request_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    svc = ApprovalService(db)
    result = svc.delete(request_id, current_user.id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Approval request not found")
    if result == "not_owner":
        raise HTTPException(status_code=403, detail="You can only delete your own requests")
    if result == "not_pending":
        raise HTTPException(status_code=409, detail="Only pending requests can be deleted")
    return ApiResponse(data=None, message="Approval request deleted", type="success")
