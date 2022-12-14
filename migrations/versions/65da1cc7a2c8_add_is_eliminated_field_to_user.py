"""Add is_eliminated field to user

Revision ID: 65da1cc7a2c8
Revises: 74c0833dc05c
Create Date: 2022-12-20 20:20:28.825810

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '65da1cc7a2c8'
down_revision = '74c0833dc05c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('is_eliminated', sa.Boolean(), nullable=False, server_default="0"))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'is_eliminated')
    # ### end Alembic commands ###
