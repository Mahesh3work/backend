"""initial tables

Revision ID: 70b43319aa90
Revises: 
Create Date: 2026-02-05 12:02:32.566581

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '70b43319aa90'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():

    # ---- explain ----
    op.create_table(
        'design_info',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('hardware', sa.String(100)),
        sa.Column('database_name', sa.String(100)),
        sa.Column('os', sa.String(100)),
        sa.Column('url', sa.String(500)),
        sa.Column('created_at', sa.TIMESTAMP(),
                  server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # ---- sales ----
    op.create_table(
        'sales_info',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('sales_date', sa.Date(), nullable=False),
        sa.Column('customer_name', sa.String(150), nullable=False),
        sa.Column('order_number', sa.String(100), nullable=False),
        sa.Column('quantity_ordered', sa.Integer(), nullable=False),
        sa.Column('invoice_number', sa.String(100)),
        sa.Column('delivery_date', sa.Date()),
        sa.Column('salesperson', sa.String(100)),
        sa.Column('price', sa.Numeric(10, 2)),
        sa.Column('remarks', sa.Text()),
        sa.Column('created_at', sa.TIMESTAMP(),
                  server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # ---- production ----
    op.create_table(
        'production_info',
        sa.Column('id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('serial_number', sa.String(100), nullable=False, unique=True),
        sa.Column('product_name', sa.String(150), nullable=False),
        sa.Column(
            'status',
            sa.Enum('Pending', 'In Progress', 'Completed', 'Rejected',
                    name='production_status_enum'),
            nullable=False
        ),
        sa.Column('created_at', sa.TIMESTAMP(),
                  server_default=sa.text('CURRENT_TIMESTAMP'))
    )

    # ---- sites_device ----
    op.create_table(
        'sites_device',
        sa.Column('device_id', sa.Integer, primary_key=True, autoincrement=True),
        sa.Column('site_id', sa.Integer, nullable=False),
        sa.Column('last_seen', sa.DateTime()),
        sa.Column('design_id', sa.Integer),
        sa.Column('sales_id', sa.Integer),
        sa.Column('production_id', sa.Integer),
        sa.Column('created_on', sa.DateTime(),
                  server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer),
        sa.Column('updated_on', sa.DateTime(),
                  server_default=sa.text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP')),
        sa.Column('updated_by', sa.Integer),

        sa.ForeignKeyConstraint(['site_id'], ['sites_sites.site_id'],
                                ondelete='CASCADE', onupdate='CASCADE'),
        sa.ForeignKeyConstraint(['design_id'], ['design_info.id']),
        sa.ForeignKeyConstraint(['sales_id'], ['sales_info.id']),
        sa.ForeignKeyConstraint(['production_id'], ['production_info.id']),
    )


def downgrade():

    op.drop_table('sites_device')
    op.drop_table('production_info')
    op.drop_table('sales_info')
    op.drop_table('design_info')
