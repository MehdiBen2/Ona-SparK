"""Add latitude and longitude to incidents

Revision ID: 186f8dedf4e2
Revises: cad30124c08d
Create Date: 2024-12-01 01:22:51.138610

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '186f8dedf4e2'
down_revision = 'cad30124c08d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('incident', schema=None) as batch_op:
        batch_op.add_column(sa.Column('latitude', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('longitude', sa.Float(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('incident', schema=None) as batch_op:
        batch_op.drop_column('longitude')
        batch_op.drop_column('latitude')

    # ### end Alembic commands ###
