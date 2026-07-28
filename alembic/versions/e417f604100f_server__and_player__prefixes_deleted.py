"""server_ and player_ prefixes deleted

Revision ID: e417f604100f
Revises: 0e7620b55f72
Create Date: 2026-05-23 18:21:12.301470

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e417f604100f'
down_revision: Union[str, Sequence[str], None] = '0e7620b55f72'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.alter_column(
        "server_snapshot_mod_associations",
        "server_snapshot_id",
        new_column_name="snapshot_id",
        existing_type=sa.Integer(),
    )

    op.alter_column(
        "server_snapshot_plugin_associations",
        "server_snapshot_id",
        new_column_name="snapshot_id",
        existing_type=sa.Integer(),
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column(
        "server_snapshot_plugin_associations",
        "snapshot_id",
        new_column_name="server_snapshot_id",
        existing_type=sa.Integer(),
    )

    op.alter_column(
        "server_snapshot_mod_associations",
        "snapshot_id",
        new_column_name="server_snapshot_id",
        existing_type=sa.Integer(),
    )