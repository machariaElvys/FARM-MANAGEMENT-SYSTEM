"""Initial schema: farmers, record categories, farm records.

Revision ID: 0001_initial
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None

DEFAULT_CATEGORIES = [
    ("planting", "Planting", 0),
    ("inputs", "Farm inputs", 1),
    ("labour", "Labour", 2),
    ("expenses", "Other expenses", 3),
    ("harvest", "Harvest", 4),
    ("sales", "Sales", 5),
]


def upgrade() -> None:
    op.create_table(
        "farmers",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_farmers_email", "farmers", ["email"], unique=True)

    op.create_table(
        "record_categories",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("name", sa.String(30), nullable=False),
        sa.Column("label", sa.String(60), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_record_categories_name", "record_categories", ["name"], unique=True)

    op.create_table(
        "farm_records",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("farmer_id", sa.String(36), nullable=False),
        sa.Column("category_id", sa.String(36), nullable=False),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("occurred_on", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("quantity", sa.Numeric(12, 2), nullable=True),
        sa.Column("unit", sa.String(40), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["farmer_id"], ["farmers.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["record_categories.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_farm_records_farmer_id", "farm_records", ["farmer_id"])
    op.create_index("ix_farm_records_category_id", "farm_records", ["category_id"])
    op.create_index("ix_farm_records_occurred_on", "farm_records", ["occurred_on"])

    import uuid

    op.bulk_insert(
        sa.table(
            "record_categories",
            sa.column("id", sa.String(36)),
            sa.column("name", sa.String(30)),
            sa.column("label", sa.String(60)),
            sa.column("sort_order", sa.Integer()),
        ),
        [
            {"id": str(uuid.uuid4()), "name": name, "label": label, "sort_order": order}
            for name, label, order in DEFAULT_CATEGORIES
        ],
    )


def downgrade() -> None:
    op.drop_table("farm_records")
    op.drop_table("record_categories")
    op.drop_table("farmers")
