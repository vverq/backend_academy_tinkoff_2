"""init

Revision ID: e4423b653a81
Revises: 
Create Date: 2023-05-15 22:00:02.001791

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e4423b653a81'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.UUID, primary_key=True, index=True),
        sa.Column("name", sa.String),
        sa.Column("description", sa.String),
        sa.Column("age", sa.Integer),
        sa.Column("email", sa.String),
        sa.Column("password", sa.String),
        sa.Column("login_date", sa.DateTime(timezone=True), default=None)
    )
    op.create_table(
        "friendship",
        sa.Column("friend_id_one", sa.UUID, sa.ForeignKey("users.id"), index=True, primary_key=True),
        sa.Column("friend_id_two", sa.UUID, sa.ForeignKey("users.id"), index=True, primary_key=True)
    )


def downgrade() -> None:
    op.drop_table("users")
    op.drop_table("friendship")
