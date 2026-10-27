"""quran ayah themes (QUL)

Revision ID: d1f2a3b4c5e6
Revises: c9e4f1a2b3d5
Create Date: 2026-10-27 05:20:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd1f2a3b4c5e6'
down_revision: Union[str, Sequence[str], None] = 'c9e4f1a2b3d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('ayah_themes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('chapter_id', sa.SmallInteger(), nullable=False),
    sa.Column('ayah_from', sa.SmallInteger(), nullable=False),
    sa.Column('ayah_to', sa.SmallInteger(), nullable=False),
    sa.Column('theme', sa.Text(), nullable=False),
    sa.Column('keywords', sa.Text(), nullable=True),
    sa.Column('total_ayahs', sa.SmallInteger(), nullable=True),
    sa.Column('raw_artifact_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['chapter_id'], ['quran.chapters.id'], name='fk_ayah_themes_chapter_id_chapters'),
    sa.ForeignKeyConstraint(['raw_artifact_id'], ['metadata.raw_artifacts.id'], name='fk_ayah_themes_raw_artifact_id_raw_artifacts'),
    sa.PrimaryKeyConstraint('id', name='pk_ayah_themes'),
    schema='quran'
    )
    op.create_index('ix_quran_ayah_themes_chapter_id', 'ayah_themes', ['chapter_id'], unique=False, schema='quran')


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('ayah_themes', schema='quran')
