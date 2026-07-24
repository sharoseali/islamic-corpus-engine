"""Declarative base for all ORM models.

Every model in the platform inherits from `Base`. A deterministic naming
convention is enforced so that Alembic autogenerate produces stable,
predictable constraint names across all environments.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Domain schemas - tables are grouped by domain instead of living in `public`.
SCHEMA_QURAN = "quran"
SCHEMA_HADITH = "hadith"
SCHEMA_TAFSIR = "tafsir"
SCHEMA_SEARCH = "search"
SCHEMA_METADATA = "metadata"

ALL_SCHEMAS = (
    SCHEMA_QURAN,
    SCHEMA_HADITH,
    SCHEMA_TAFSIR,
    SCHEMA_SEARCH,
    SCHEMA_METADATA,
)

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)
