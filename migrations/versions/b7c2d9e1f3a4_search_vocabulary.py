"""search vocabulary for spelling suggestions; drop the document trigram index

Revision ID: b7c2d9e1f3a4
Revises: a3f1c2d4e5b6
Create Date: 2026-10-27 02:40:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b7c2d9e1f3a4'
down_revision: Union[str, Sequence[str], None] = 'a3f1c2d4e5b6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('vocabulary',
    sa.Column('language_code', sa.String(length=8), nullable=False),
    sa.Column('lexeme', sa.Text(), nullable=False),
    sa.Column('ndoc', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('language_code', 'lexeme', name='pk_vocabulary'),
    schema='search'
    )
    op.execute("CREATE INDEX ix_search_vocabulary_trgm ON search.vocabulary USING gin (lexeme gin_trgm_ops)")
    # Spelling help now matches the vocabulary, not whole documents.
    op.execute("DROP INDEX IF EXISTS search.ix_search_documents_trgm")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("CREATE INDEX ix_search_documents_trgm ON search.documents USING gin (text_normalized gin_trgm_ops)")
    op.drop_table('vocabulary', schema='search')
