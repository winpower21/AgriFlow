"""add compensation types and validations

Revision ID: a0be8d365925
Revises: 8fa548e4f38c
Create Date: 2026-03-22 20:27:40.445946

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a0be8d365925'
down_revision: Union[str, Sequence[str], None] = '8fa548e4f38c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()

    # --- Pre-check: fail if any vehicles have NULL fuel_consumable_id ---
    null_count = conn.execute(
        sa.text("SELECT COUNT(*) FROM vehicles WHERE fuel_consumable_id IS NULL")
    ).scalar()
    if null_count > 0:
        raise ValueError(
            f"{null_count} vehicle(s) have no fuel consumable assigned. "
            "Please assign a fuel consumable to all vehicles via the UI before running this migration."
        )

    # --- Structural changes ---
    op.add_column('expenses', sa.Column('personnel_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'expenses', 'personnel', ['personnel_id'], ['id'], ondelete='SET NULL')
    op.add_column('personnel', sa.Column('salary_payment_date', sa.Integer(), nullable=True))
    op.alter_column('vehicles', 'fuel_consumable_id',
               existing_type=sa.INTEGER(),
               nullable=False)
    # Add calculation_method as nullable first, then populate, then make NOT NULL
    op.add_column('wage_types', sa.Column('calculation_method', sa.String(length=20), nullable=True))

    # --- Data operations ---

    # Set calculation_method on existing wage types
    conn.execute(sa.text("""
        UPDATE wage_types SET calculation_method = CASE
            WHEN LOWER(name) LIKE '%daily%' OR LOWER(name) LIKE '%day%' THEN 'DAILY'
            WHEN LOWER(name) LIKE '%kg%' OR LOWER(name) LIKE '%output%' OR LOWER(name) LIKE '%piece%' THEN 'OUTPUT'
            WHEN LOWER(name) LIKE '%month%' OR LOWER(name) LIKE '%salary%' THEN 'MONTHLY'
            ELSE 'DAILY'
        END
    """))

    # Now make it NOT NULL
    op.alter_column('wage_types', 'calculation_method',
               existing_type=sa.String(length=20),
               nullable=False)

    # Seed Salary (Monthly) wage type if no MONTHLY type exists
    monthly_exists = conn.execute(
        sa.text("SELECT COUNT(*) FROM wage_types WHERE calculation_method = 'MONTHLY'")
    ).scalar()
    if not monthly_exists:
        conn.execute(sa.text(
            "INSERT INTO wage_types (name, calculation_method) VALUES ('Salary (Monthly)', 'MONTHLY')"
        ))


def downgrade() -> None:
    """Downgrade schema."""
    conn = op.get_bind()

    # Remove seeded salary wage type
    conn.execute(sa.text(
        "DELETE FROM wage_types WHERE name = 'Salary (Monthly)' AND calculation_method = 'MONTHLY'"
    ))

    op.drop_column('wage_types', 'calculation_method')
    op.alter_column('vehicles', 'fuel_consumable_id',
               existing_type=sa.INTEGER(),
               nullable=True)
    op.drop_column('personnel', 'salary_payment_date')
    op.drop_constraint(None, 'expenses', type_='foreignkey')
    op.drop_column('expenses', 'personnel_id')
