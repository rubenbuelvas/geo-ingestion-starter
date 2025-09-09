"""
Revision ID: 0001_init
Revises:
Create Date: 2025-09-04
"""
from alembic import op
import sqlalchemy as sa
import sqlalchemy.dialects.postgresql as pg
from geoalchemy2 import Geography

revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    op.create_table(
        "features",
        sa.Column("id", pg.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("geom", Geography(geometry_type="POINT", srid=4326, spatial_index=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(), nullable=False),
    )
    op.create_table(
        "footprints",
        sa.Column("feature_id", pg.UUID(as_uuid=True), sa.ForeignKey("features.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("buffer_m", sa.Integer(), nullable=False),
        sa.Column("area_m2", pg.DOUBLE_PRECISION(), nullable=False),
        sa.Column("geom", Geography(geometry_type="POINT", srid=4326, spatial_index=True), nullable=False),
    )

def downgrade():
    op.drop_table("footprints")
    op.drop_table("features")
    op.execute("DROP EXTENSION IF EXISTS postgis;")
