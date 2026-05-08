"""Shared SQLAlchemy declarative base and metadata naming convention.

A deterministic naming convention is configured on the shared
:class:`MetaData` so that index, unique, foreign-key, primary-key, and
check constraint names are generated predictably. Stable constraint
names matter for two reasons:

* Alembic auto-generated migrations diff cleanly between environments
  rather than producing churn from auto-named constraints.
* Future migration to PostgreSQL is straightforward because every
  constraint already has a portable, explicit name.

ORM model modules subclass :class:`Base` and rely on this metadata
without further configuration.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
"""Standard naming pattern applied to every constraint and index."""


class Base(DeclarativeBase):
    """Declarative base inherited by every ORM model in the package.

    Carries a shared :class:`MetaData` instance configured with
    :data:`NAMING_CONVENTION`. Subclasses simply set ``__tablename__``
    and define mapped columns; constraint names are generated from the
    convention without further intervention.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


__all__ = ["Base", "NAMING_CONVENTION"]
