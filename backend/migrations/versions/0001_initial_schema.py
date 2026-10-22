"""Initial schema of the Palmprint Research Platform.

Creates the tables ``users``, ``images``, ``processing_jobs``, ``experiments``,
``experiment_results`` and ``reports`` together with the indexes required by
the frequently queried columns.

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-22
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("is_demo_account", sa.Boolean(), nullable=False),
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_users_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_users_email"), ["email"], unique=True)

    op.create_table(
        "experiments",
        sa.Column("owner_id", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("operation", sa.String(length=64), nullable=False),
        sa.Column("algorithm", sa.String(length=64), nullable=False),
        sa.Column("parameters_json", sa.Text(), nullable=False),
        sa.Column("image_ids_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("report_id", sa.String(length=32), nullable=True),
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_experiments_owner_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_experiments")),
    )
    with op.batch_alter_table("experiments", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_experiments_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_experiments_owner_id"), ["owner_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_experiments_status"), ["status"], unique=False)

    op.create_table(
        "images",
        sa.Column("owner_id", sa.String(length=32), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("media_type", sa.String(length=64), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=120), nullable=True),
        sa.Column("subject_id", sa.String(length=120), nullable=True),
        sa.Column("notes", sa.String(length=500), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_images_owner_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_images")),
    )
    with op.batch_alter_table("images", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_images_checksum_sha256"), ["checksum_sha256"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_images_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_images_label"), ["label"], unique=False)
        batch_op.create_index(batch_op.f("ix_images_owner_id"), ["owner_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_images_storage_key"), ["storage_key"], unique=True)
        batch_op.create_index(batch_op.f("ix_images_subject_id"), ["subject_id"], unique=False)

    op.create_table(
        "reports",
        sa.Column("owner_id", sa.String(length=32), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("report_type", sa.String(length=48), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("experiment_id", sa.String(length=32), nullable=True),
        sa.Column("job_id", sa.String(length=32), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_reports_owner_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reports")),
        sa.UniqueConstraint("storage_key", name=op.f("uq_reports_storage_key")),
    )
    with op.batch_alter_table("reports", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_reports_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_reports_experiment_id"), ["experiment_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_reports_job_id"), ["job_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_reports_owner_id"), ["owner_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_reports_report_type"), ["report_type"], unique=False)
        batch_op.create_index(batch_op.f("ix_reports_status"), ["status"], unique=False)

    op.create_table(
        "experiment_results",
        sa.Column("experiment_id", sa.String(length=32), nullable=False),
        sa.Column("kind", sa.String(length=48), nullable=False),
        sa.Column("label", sa.String(length=160), nullable=True),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("unit", sa.String(length=24), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
        sa.Column("image_id", sa.String(length=32), nullable=True),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["experiment_id"],
            ["experiments.id"],
            name=op.f("fk_experiment_results_experiment_id_experiments"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_experiment_results")),
    )
    with op.batch_alter_table("experiment_results", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_experiment_results_created_at"), ["created_at"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_experiment_results_experiment_id"), ["experiment_id"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_experiment_results_kind"), ["kind"], unique=False)

    op.create_table(
        "processing_jobs",
        sa.Column("owner_id", sa.String(length=32), nullable=False),
        sa.Column("image_id", sa.String(length=32), nullable=True),
        sa.Column("operation", sa.String(length=64), nullable=False),
        sa.Column("algorithm", sa.String(length=64), nullable=False),
        sa.Column("algorithm_version", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("parameters_json", sa.Text(), nullable=False),
        sa.Column("result_json", sa.Text(), nullable=True),
        sa.Column("metrics_json", sa.Text(), nullable=True),
        sa.Column("warnings_json", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["image_id"],
            ["images.id"],
            name=op.f("fk_processing_jobs_image_id_images"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_processing_jobs")),
    )
    with op.batch_alter_table("processing_jobs", schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f("ix_processing_jobs_algorithm"), ["algorithm"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_processing_jobs_created_at"), ["created_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_processing_jobs_image_id"), ["image_id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_processing_jobs_operation"), ["operation"], unique=False
        )
        batch_op.create_index(batch_op.f("ix_processing_jobs_owner_id"), ["owner_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_processing_jobs_status"), ["status"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("processing_jobs", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_processing_jobs_status"))
        batch_op.drop_index(batch_op.f("ix_processing_jobs_owner_id"))
        batch_op.drop_index(batch_op.f("ix_processing_jobs_operation"))
        batch_op.drop_index(batch_op.f("ix_processing_jobs_image_id"))
        batch_op.drop_index(batch_op.f("ix_processing_jobs_created_at"))
        batch_op.drop_index(batch_op.f("ix_processing_jobs_algorithm"))
    op.drop_table("processing_jobs")

    with op.batch_alter_table("experiment_results", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_experiment_results_kind"))
        batch_op.drop_index(batch_op.f("ix_experiment_results_experiment_id"))
        batch_op.drop_index(batch_op.f("ix_experiment_results_created_at"))
    op.drop_table("experiment_results")

    with op.batch_alter_table("reports", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_reports_status"))
        batch_op.drop_index(batch_op.f("ix_reports_report_type"))
        batch_op.drop_index(batch_op.f("ix_reports_owner_id"))
        batch_op.drop_index(batch_op.f("ix_reports_job_id"))
        batch_op.drop_index(batch_op.f("ix_reports_experiment_id"))
        batch_op.drop_index(batch_op.f("ix_reports_created_at"))
    op.drop_table("reports")

    with op.batch_alter_table("images", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_images_subject_id"))
        batch_op.drop_index(batch_op.f("ix_images_storage_key"))
        batch_op.drop_index(batch_op.f("ix_images_owner_id"))
        batch_op.drop_index(batch_op.f("ix_images_label"))
        batch_op.drop_index(batch_op.f("ix_images_created_at"))
        batch_op.drop_index(batch_op.f("ix_images_checksum_sha256"))
    op.drop_table("images")

    with op.batch_alter_table("experiments", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_experiments_status"))
        batch_op.drop_index(batch_op.f("ix_experiments_owner_id"))
        batch_op.drop_index(batch_op.f("ix_experiments_created_at"))
    op.drop_table("experiments")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_users_email"))
        batch_op.drop_index(batch_op.f("ix_users_created_at"))
    op.drop_table("users")
