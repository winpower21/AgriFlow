from decimal import Decimal
from typing import List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session, joinedload

from ..models.batch import Batch, BatchStage
from ..schemas.batch import BatchUpdate


class BatchService:
    def __init__(self, db: Session):
        self.db = db

    def get_stages(self) -> List[BatchStage]:
        return self.db.query(BatchStage).order_by(BatchStage.batch_stage_level).all()

    def get_harvest_stage(self) -> Optional[BatchStage]:
        return (
            self.db.query(BatchStage).filter(BatchStage.name.ilike("HARVEST%")).first()
        )

    def get_all(
        self,
        stage_id: Optional[int] = None,
        plantation_id: Optional[int] = None,
        is_depleted: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> List[Batch]:
        q = self.db.query(Batch).options(
            joinedload(Batch.stage), joinedload(Batch.plantation)
        )
        if stage_id is not None:
            q = q.filter(Batch.stage_id == stage_id)
        if plantation_id is not None:
            q = q.filter(Batch.plantation_id == plantation_id)
        if is_depleted is not None:
            q = q.filter(Batch.is_depleted == is_depleted)
        if search:
            q = q.filter(Batch.batch_code.ilike(f"%{search}%"))
        return q.order_by(Batch.created_at.desc()).all()

    def get_by_id(self, batch_id: int) -> Optional[Batch]:
        return (
            self.db.query(Batch)
            .options(joinedload(Batch.stage), joinedload(Batch.plantation))
            .filter(Batch.id == batch_id)
            .first()
        )

    def update(self, batch_id: int, data: BatchUpdate) -> Optional[Batch]:
        obj = self.db.query(Batch).filter(Batch.id == batch_id).first()
        if not obj:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, field, value)
        self.db.commit()
        return self.get_by_id(batch_id)

    def delete(self, batch_id: int) -> Optional[str]:
        """Returns None on success, 'not_found', or 'in_use'."""
        from ..models.transformation import TransformationInput, TransformationOutput

        obj = self.db.query(Batch).filter(Batch.id == batch_id).first()
        if not obj:
            return "not_found"
        in_input = (
            self.db.query(TransformationInput)
            .filter(TransformationInput.batch_id == batch_id)
            .first()
        )
        in_output = (
            self.db.query(TransformationOutput)
            .filter(TransformationOutput.batch_id == batch_id)
            .first()
        )
        if in_input or in_output:
            return "in_use"
        self.db.delete(obj)
        self.db.commit()
        return None

    def get_transformations_for_batch(self, batch_id: int) -> list:
        """Return all transformations where this batch is an input or an output,
        ordered by from_date ascending (creation → consumption order).
        Each item includes a `role` field: 'output' (batch was produced here)
        or 'input' (batch was consumed here)."""
        from sqlalchemy import exists, or_
        from sqlalchemy.orm import joinedload

        from ..models.transformation import (
            Transformation,
            TransformationInput,
            TransformationOutput,
        )

        rows = (
            self.db.query(Transformation)
            .options(joinedload(Transformation.transformation_type))
            .filter(
                or_(
                    exists().where(
                        TransformationInput.transformation_id == Transformation.id,
                        TransformationInput.batch_id == batch_id,
                    ),
                    exists().where(
                        TransformationOutput.transformation_id == Transformation.id,
                        TransformationOutput.batch_id == batch_id,
                    ),
                )
            )
            .order_by(Transformation.from_date.asc())
            .all()
        )

        # Determine role for each transformation
        input_t_ids = {
            row.transformation_id
            for row in self.db.query(TransformationInput.transformation_id)
            .filter(TransformationInput.batch_id == batch_id)
            .all()
        }
        output_t_ids = {
            row.transformation_id
            for row in self.db.query(TransformationOutput.transformation_id)
            .filter(TransformationOutput.batch_id == batch_id)
            .all()
        }

        result = []
        for t in rows:
            result.append(
                {
                    "id": t.id,
                    "type_id": t.type_id,
                    "type_name": t.transformation_type.name
                    if t.transformation_type
                    else None,
                    "from_date": t.from_date,
                    "to_date": t.to_date,
                    "notes": t.notes,
                    "is_complete": t.to_date is not None,
                    # A batch can theoretically be both input and output in a transformation
                    # (unusual, but we handle it). If only in output_t_ids → 'output'.
                    "role": "input" if t.id in input_t_ids else "output",
                }
            )
        return result

    def get_genealogy(self, batch_id: int) -> dict:
        """Build ancestor+descendant tree using batch_parents table.

        Uses separate ancestor/descendant traversal functions that always
        create fresh dicts, so no Python object is ever shared between two
        positions in the tree.  This prevents the cyclic-reference error that
        Pydantic raises when the same object appears in both a parent's
        `children` list and a child's `parents` list.
        """
        sql = text("""
            WITH RECURSIVE ancestors AS (
                SELECT b.id, b.batch_code, b.remaining_weight_kg, b.is_depleted,
                       bs.name AS stage_name
                FROM batches b
                LEFT JOIN batch_stages bs ON b.stage_id = bs.id
                WHERE b.id = :batch_id
                UNION ALL
                SELECT b.id, b.batch_code, b.remaining_weight_kg, b.is_depleted,
                       bs.name AS stage_name
                FROM batch_parents bp
                INNER JOIN ancestors a ON bp.child_batch_id = a.id
                INNER JOIN batches b ON bp.parent_batch_id = b.id
                LEFT JOIN batch_stages bs ON b.stage_id = bs.id
            ),
            descendants AS (
                SELECT b.id, b.batch_code, b.remaining_weight_kg, b.is_depleted,
                       bs.name AS stage_name
                FROM batches b
                LEFT JOIN batch_stages bs ON b.stage_id = bs.id
                WHERE b.id = :batch_id
                UNION ALL
                SELECT b.id, b.batch_code, b.remaining_weight_kg, b.is_depleted,
                       bs.name AS stage_name
                FROM batch_parents bp
                INNER JOIN descendants d ON bp.parent_batch_id = d.id
                INNER JOIN batches b ON bp.child_batch_id = b.id
                LEFT JOIN batch_stages bs ON b.stage_id = bs.id
            ),
            edges AS (
                SELECT child_batch_id, parent_batch_id FROM batch_parents
                WHERE child_batch_id IN (SELECT id FROM ancestors UNION SELECT id FROM descendants)
                   OR parent_batch_id IN (SELECT id FROM ancestors UNION SELECT id FROM descendants)
            )
            SELECT 'node' AS row_type, id, batch_code, remaining_weight_kg, is_depleted,
                   stage_name, NULL::int AS child_id, NULL::int AS parent_id
            FROM (SELECT * FROM ancestors UNION SELECT * FROM descendants) all_nodes
            UNION ALL
            SELECT 'edge' AS row_type, NULL, NULL, NULL, NULL, NULL,
                   child_batch_id, parent_batch_id
            FROM edges
        """)
        rows = self.db.execute(sql, {"batch_id": batch_id}).fetchall()

        # Flat node data — no cross-references, just raw field values.
        node_data: dict[int, dict] = {}
        # parent_map[child_id] = [parent_id, ...]
        parent_map: dict[int, list[int]] = {}
        # child_map[parent_id] = [child_id, ...]
        child_map: dict[int, list[int]] = {}

        for row in rows:
            if row.row_type == "node" and row.id not in node_data:
                node_data[row.id] = {
                    "batch_id": row.id,
                    "batch_code": row.batch_code,
                    "stage_name": row.stage_name,
                    "remaining_weight_kg": row.remaining_weight_kg,
                    "is_depleted": row.is_depleted,
                }
                parent_map[row.id] = []
                child_map[row.id] = []
            elif row.row_type == "edge":
                cid, pid = row.child_id, row.parent_id
                if cid in parent_map and pid not in parent_map[cid]:
                    parent_map[cid].append(pid)
                if pid in child_map and cid not in child_map[pid]:
                    child_map[pid].append(cid)

        def build_ancestors(nid: int, visited: frozenset) -> dict:
            """Return a NEW dict for nid that recurses only upward (parents).
            `children` is always [] to prevent cross-links back to descendants."""
            data = {
                **node_data[nid],
                "children": [],
                "parents": [
                    build_ancestors(pid, visited | {nid})
                    for pid in parent_map.get(nid, [])
                    if pid in node_data and pid not in visited
                ],
            }
            return data

        def build_descendants(nid: int, visited: frozenset) -> dict:
            """Return a NEW dict for nid that recurses only downward (children).
            `parents` is always [] to prevent cross-links back to ancestors."""
            data = {
                **node_data[nid],
                "parents": [],
                "children": [
                    build_descendants(cid, visited | {nid})
                    for cid in child_map.get(nid, [])
                    if cid in node_data and cid not in visited
                ],
            }
            return data

        if batch_id not in node_data:
            batch = self.get_by_id(batch_id)
            if batch:
                return {
                    "batch_id": batch.id,
                    "batch_code": batch.batch_code,
                    "stage_name": batch.stage.name if batch.stage else None,
                    "remaining_weight_kg": batch.remaining_weight_kg,
                    "is_depleted": batch.is_depleted,
                    "parents": [],
                    "children": [],
                }
            return {
                "batch_id": batch_id,
                "batch_code": "Unknown",
                "stage_name": None,
                "remaining_weight_kg": Decimal("0"),
                "is_depleted": False,
                "parents": [],
                "children": [],
            }

        # Root node: ancestors go up, descendants go down.
        # Each direction uses its own traversal so no dict is ever shared.
        # pid/cid != batch_id guards against self-referencing batch_parents rows.
        return {
            **node_data[batch_id],
            "parents": [
                build_ancestors(pid, frozenset({batch_id}))
                for pid in parent_map.get(batch_id, [])
                if pid in node_data and pid != batch_id
            ],
            "children": [
                build_descendants(cid, frozenset({batch_id}))
                for cid in child_map.get(batch_id, [])
                if cid in node_data and cid != batch_id
            ],
        }
