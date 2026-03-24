from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..core.dependencies import get_current_user, roles_required
from ..crud.batch import BatchService
from ..database import get_db
from ..schemas.batch import BatchDetail, BatchGenealogyNode, BatchListItem, BatchUpdate
from ..schemas.response import ApiResponse

router = APIRouter(
    prefix="/batches",
    tags=["batches"],
    dependencies=[Depends(get_current_user)],
)


def _to_list_item(batch) -> dict:
    return {
        "id": batch.id,
        "batch_code": batch.batch_code,
        "plantation_id": batch.plantation_id,
        "plantation_name": batch.plantation.name if batch.plantation else None,
        "stage_id": batch.stage_id,
        "stage_name": batch.stage.name if batch.stage else None,
        "initial_weight_kg": batch.initial_weight_kg,
        "remaining_weight_kg": batch.remaining_weight_kg,
        "is_depleted": batch.is_depleted,
        "notes": batch.notes,
        "created_at": batch.created_at,
    }


def _to_detail(batch) -> dict:
    return {
        "id": batch.id,
        "batch_code": batch.batch_code,
        "plantation_id": batch.plantation_id,
        "plantation_name": batch.plantation.name if batch.plantation else None,
        "stage_id": batch.stage_id,
        "stage_name": batch.stage.name if batch.stage else None,
        "initial_weight_kg": batch.initial_weight_kg,
        "remaining_weight_kg": batch.remaining_weight_kg,
        "is_depleted": batch.is_depleted,
        "notes": batch.notes,
        "created_at": batch.created_at,
        "updated_at": batch.updated_at,
    }


@router.get("/stages", response_model=ApiResponse[list[dict]])
def list_stages(db: Session = Depends(get_db)):
    stages = BatchService(db).get_stages()
    return ApiResponse(data=[{"id": s.id, "name": s.name} for s in stages])


@router.get("/", response_model=ApiResponse[list[BatchListItem]])
def list_batches(
    stage_id: Optional[int] = Query(None),
    plantation_id: Optional[int] = Query(None),
    is_depleted: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    batches = BatchService(db).get_all(
        stage_id=stage_id,
        plantation_id=plantation_id,
        is_depleted=is_depleted,
        search=search,
    )
    return ApiResponse(data=[_to_list_item(b) for b in batches])



@router.get("/{batch_id}/transformations", response_model=ApiResponse[list[dict]])
def get_batch_transformations(batch_id: int, db: Session = Depends(get_db)):
    """All transformations where this batch appears as input or output,
    ordered chronologically. Includes a `role` field ('input'|'output')."""
    items = BatchService(db).get_transformations_for_batch(batch_id)
    if not items:
        batch = BatchService(db).get_by_id(batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
    return ApiResponse(data=items)


@router.get("/{batch_id}/genealogy", response_model=ApiResponse[BatchGenealogyNode])
def get_batch_genealogy(batch_id: int, db: Session = Depends(get_db)):
    return ApiResponse(data=BatchService(db).get_genealogy(batch_id))


@router.get("/{batch_id}", response_model=ApiResponse[BatchDetail])
def get_batch(batch_id: int, db: Session = Depends(get_db)):
    batch = BatchService(db).get_by_id(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return ApiResponse(data=_to_detail(batch))


@router.put("/{batch_id}", response_model=ApiResponse[BatchDetail],
            dependencies=[Depends(roles_required("admin"))])
def update_batch(batch_id: int, data: BatchUpdate, db: Session = Depends(get_db)):
    batch = BatchService(db).update(batch_id, data)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return ApiResponse(data=_to_detail(batch), message="Batch updated successfully", type="success")


@router.delete("/{batch_id}", response_model=ApiResponse[None],
               dependencies=[Depends(roles_required("admin"))])
def delete_batch(batch_id: int, db: Session = Depends(get_db)):
    result = BatchService(db).delete(batch_id)
    if result == "not_found":
        raise HTTPException(status_code=404, detail="Batch not found")
    if result == "in_use":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Batch cannot be deleted: it is referenced by one or more transformations",
        )
    if result == "completed_transformation_output":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot delete a batch that is an output of a completed transformation",
        )
    return ApiResponse(data=None, message="Batch deleted successfully", type="success")
