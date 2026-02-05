"""SQLAlchemy declarative Base for migrations only. No app config.

Alembic and any migration tool must import Base from here so they never
load JWT_SECRET_KEY or other runtime settings. Runtime code can keep
using app.core.database, which imports Base from here and adds engine/sessions.
"""
from sqlalchemy.orm import declarative_base

Base = declarative_base()
