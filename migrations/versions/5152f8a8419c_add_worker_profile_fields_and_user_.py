"""Add worker profile fields and user relationship

Revision ID: 5152f8a8419c
Revises: 6523c69373c5
Create Date: 2024-12-07 21:14:49.579239

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5152f8a8419c'
down_revision = '6523c69373c5'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('worker', schema=None) as batch_op:
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('profile_image', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('phone', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('email', sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column('address', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('emergency_contact', sa.String(length=200), nullable=True))
        batch_op.create_unique_constraint(None, ['user_id'])
        batch_op.create_foreign_key(None, 'user', ['user_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('worker', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')
        batch_op.drop_constraint(None, type_='unique')
        batch_op.drop_column('emergency_contact')
        batch_op.drop_column('address')
        batch_op.drop_column('email')
        batch_op.drop_column('phone')
        batch_op.drop_column('profile_image')
        batch_op.drop_column('user_id')

    # ### end Alembic commands ###
