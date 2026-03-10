"""link_consumable_purchase_to_expense

Revision ID: a1c3f7e82d50
Revises: 9bac82a0e87e
Create Date: 2026-03-10

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1c3f7e82d50'
down_revision: Union[str, Sequence[str], None] = '9bac82a0e87e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'consumable_purchases',
        sa.Column('expense_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_consumable_purchases_expense_id',
        'consumable_purchases',
        'expenses',
        ['expense_id'],
        ['id'],
    )


def downgrade() -> None:
    op.drop_constraint(
        'fk_consumable_purchases_expense_id',
        'consumable_purchases',
        type_='foreignkey',
    )
    op.drop_column('consumable_purchases', 'expense_id')
