"""create domain schemas and extensions

Revision ID: fe39341376e1
Revises:
Create Date: 2026-07-17 00:20:03.274122

Foundation of the Islamic Knowledge Core database:

- Domain schemas so tables are grouped by domain instead of `public`:
    quran     — canonical Quran text, readings, translations
    hadith    — hadith collections, chains, gradings
    tafsir    — exegesis works linked to Quran ayat
    search    — normalized/indexed text for retrieval (derived data)
    metadata  — sources, licenses, checksums, import provenance
- Extensions:
    vector    — pgvector, for future semantic search embeddings
    pg_trgm   — trigram matching, for fuzzy text lookup
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'fe39341376e1'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMAS = ("quran", "hadith", "tafsir", "search", "metadata")


def upgrade() -> None:
    """Create domain schemas and extensions."""
    for schema in SCHEMAS:
        op.execute(f'CREATE SCHEMA IF NOT EXISTS "{schema}"')
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")


def downgrade() -> None:
    """Drop domain schemas and extensions."""
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    op.execute("DROP EXTENSION IF EXISTS vector")
    for schema in reversed(SCHEMAS):
        op.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
