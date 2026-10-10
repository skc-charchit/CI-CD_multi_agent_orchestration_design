"""Declarative base for SQLAlchemy persistence models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class inherited by SQLAlchemy models."""
