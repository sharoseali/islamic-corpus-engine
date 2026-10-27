"""search chunks (embeddings) and embedding state

Revision ID: a3f1c2d4e5b6
Revises: dbc6af6c6974
Create Date: 2026-10-26 18:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision: str = 'a3f1c2d4e5b6'
down_revision: Union[str, Sequence[str], None] = 'dbc6af6c6974'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

EMBEDDING_DIM = 1024


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('chunks',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('document_id', sa.BigInteger(), nullable=False),
    sa.Column('chunk_index', sa.SmallInteger(), nullable=False),
    sa.Column('doc_type', sa.String(length=32), nullable=False),
    sa.Column('language_code', sa.String(length=8), nullable=False),
    sa.Column('collection_key', sa.String(length=64), nullable=False),
    sa.Column('text', sa.Text(), nullable=False),
    sa.Column('char_start', sa.Integer(), nullable=False),
    sa.Column('char_end', sa.Integer(), nullable=False),
    sa.Column('embedding', Vector(EMBEDDING_DIM), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['search.documents.id'], name=op.f('fk_chunks_document_id_documents'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_chunks')),
    sa.UniqueConstraint('document_id', 'chunk_index', name='chunk_identity'),
    schema='search'
    )
    op.create_index('ix_search_chunks_type_lang', 'chunks', ['doc_type', 'language_code'], unique=False, schema='search')
    # HNSW index for cosine nearest-neighbour search. Built now on the empty
    # table; pgvector maintains it as rows are inserted.
    op.create_index('ix_search_chunks_embedding', 'chunks', ['embedding'], unique=False, schema='search',
                    postgresql_using='hnsw', postgresql_with={'m': 32, 'ef_construction': 256},
                    postgresql_ops={'embedding': 'vector_cosine_ops'})
    op.create_table('embedding_state',
    sa.Column('id', sa.SmallInteger(), nullable=False),
    sa.Column('built_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('model_name', sa.String(length=128), nullable=False),
    sa.Column('model_dim', sa.Integer(), nullable=False),
    sa.Column('model_files', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('chunker_version', sa.String(length=32), nullable=False),
    sa.Column('chunk_count', sa.Integer(), nullable=False),
    sa.Column('documents_indexed', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_embedding_state')),
    schema='search'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('embedding_state', schema='search')
    op.drop_index('ix_search_chunks_embedding', table_name='chunks', schema='search')
    op.drop_index('ix_search_chunks_type_lang', table_name='chunks', schema='search')
    op.drop_table('chunks', schema='search')
