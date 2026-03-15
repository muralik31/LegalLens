"""Sync schema with models

Revision ID: 002
Revises: 001
Create Date: 2026-03-15

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add updated_at column to users table
    op.add_column('users', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))

    # Rename file_path to storage_path in documents table
    op.alter_column('documents', 'file_path', new_column_name='storage_path')

    # Rename analysis_result to analysis in documents table
    op.alter_column('documents', 'analysis_result', new_column_name='analysis')

    # Add extracted_text column to documents table
    op.add_column('documents', sa.Column('extracted_text', sa.Text(), nullable=False, server_default=''))

    # Remove server_default after adding the column (we only need it for migration)
    op.alter_column('documents', 'extracted_text', server_default=None)


def downgrade() -> None:
    # Reverse the changes
    op.alter_column('documents', 'extracted_text', server_default=sa.text("''"))
    op.drop_column('documents', 'extracted_text')
    op.alter_column('documents', 'analysis', new_column_name='analysis_result')
    op.alter_column('documents', 'storage_path', new_column_name='file_path')
    op.drop_column('users', 'updated_at')
