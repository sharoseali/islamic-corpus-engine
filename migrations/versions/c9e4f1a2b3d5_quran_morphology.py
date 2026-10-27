"""quran morphology: roots, lemmas, stems, words

Revision ID: c9e4f1a2b3d5
Revises: b7c2d9e1f3a4
Create Date: 2026-10-27 04:10:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'c9e4f1a2b3d5'
down_revision: Union[str, Sequence[str], None] = 'b7c2d9e1f3a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('roots',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('letters', sa.String(length=8), nullable=False),
    sa.Column('letters_spaced', sa.String(length=16), nullable=False),
    sa.Column('buckwalter', sa.String(length=16), nullable=True),
    sa.Column('words_count', sa.Integer(), nullable=True),
    sa.Column('uniq_words_count', sa.Integer(), nullable=True),
    sa.Column('raw_artifact_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['raw_artifact_id'], ['metadata.raw_artifacts.id'], name='fk_roots_raw_artifact_id_raw_artifacts'),
    sa.PrimaryKeyConstraint('id', name='pk_roots'),
    schema='quran'
    )
    op.create_index('ix_quran_roots_letters', 'roots', ['letters'], unique=False, schema='quran')
    op.create_table('lemmas',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('text', sa.String(length=64), nullable=False),
    sa.Column('text_clean', sa.String(length=64), nullable=False),
    sa.Column('raw_artifact_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['raw_artifact_id'], ['metadata.raw_artifacts.id'], name='fk_lemmas_raw_artifact_id_raw_artifacts'),
    sa.PrimaryKeyConstraint('id', name='pk_lemmas'),
    schema='quran'
    )
    op.create_index('ix_quran_lemmas_text_clean', 'lemmas', ['text_clean'], unique=False, schema='quran')
    op.create_table('stems',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('text', sa.String(length=64), nullable=False),
    sa.Column('text_clean', sa.String(length=64), nullable=False),
    sa.Column('raw_artifact_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['raw_artifact_id'], ['metadata.raw_artifacts.id'], name='fk_stems_raw_artifact_id_raw_artifacts'),
    sa.PrimaryKeyConstraint('id', name='pk_stems'),
    schema='quran'
    )
    op.create_index('ix_quran_stems_text_clean', 'stems', ['text_clean'], unique=False, schema='quran')
    op.create_table('words',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('verse_id', sa.Integer(), nullable=False),
    sa.Column('position', sa.SmallInteger(), nullable=False),
    sa.Column('text_uthmani', sa.Text(), nullable=False),
    sa.Column('text_normalized', sa.String(length=64), nullable=False),
    sa.Column('root_id', sa.Integer(), nullable=True),
    sa.Column('lemma_id', sa.Integer(), nullable=True),
    sa.Column('stem_id', sa.Integer(), nullable=True),
    sa.Column('raw_artifact_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['lemma_id'], ['quran.lemmas.id'], name='fk_words_lemma_id_lemmas'),
    sa.ForeignKeyConstraint(['raw_artifact_id'], ['metadata.raw_artifacts.id'], name='fk_words_raw_artifact_id_raw_artifacts'),
    sa.ForeignKeyConstraint(['root_id'], ['quran.roots.id'], name='fk_words_root_id_roots'),
    sa.ForeignKeyConstraint(['stem_id'], ['quran.stems.id'], name='fk_words_stem_id_stems'),
    sa.ForeignKeyConstraint(['verse_id'], ['quran.verses.id'], name='fk_words_verse_id_verses'),
    sa.PrimaryKeyConstraint('id', name='pk_words'),
    sa.UniqueConstraint('verse_id', 'position', name='uq_word_position'),
    schema='quran'
    )
    for col in ('verse_id', 'text_normalized', 'root_id', 'lemma_id', 'stem_id'):
        op.create_index(f'ix_quran_words_{col}', 'words', [col], unique=False, schema='quran')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('words', schema='quran')
    op.drop_table('stems', schema='quran')
    op.drop_table('lemmas', schema='quran')
    op.drop_table('roots', schema='quran')
