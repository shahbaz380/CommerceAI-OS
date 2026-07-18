"""Lightweight specification helpers for composable query filters."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from sqlalchemy import ColumnElement, Select, true
from sqlalchemy.orm import DeclarativeBase

T = TypeVar("T", bound=DeclarativeBase)


class Specification(ABC, Generic[T]):
    """Boolean filter applied to a SQLAlchemy select."""

    @abstractmethod
    def to_clause(self, model: type[T]) -> ColumnElement[bool]:
        raise NotImplementedError

    def apply(self, stmt: Select[Any], model: type[T]) -> Select[Any]:
        return stmt.where(self.to_clause(model))

    def __and__(self, other: Specification[T]) -> Specification[T]:
        return AndSpec(self, other)

    def __or__(self, other: Specification[T]) -> Specification[T]:
        return OrSpec(self, other)


class TrueSpec(Specification[T]):
    def to_clause(self, model: type[T]) -> ColumnElement[bool]:
        return true()


class AndSpec(Specification[T]):
    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        self.left = left
        self.right = right

    def to_clause(self, model: type[T]) -> ColumnElement[bool]:
        return self.left.to_clause(model) & self.right.to_clause(model)


class OrSpec(Specification[T]):
    def __init__(self, left: Specification[T], right: Specification[T]) -> None:
        self.left = left
        self.right = right

    def to_clause(self, model: type[T]) -> ColumnElement[bool]:
        return self.left.to_clause(model) | self.right.to_clause(model)


class TenantIdSpec(Specification[T]):
    """Filter by workspace_id when model has TenantOwnedMixin."""

    def __init__(self, workspace_id: uuid.UUID) -> None:
        self.workspace_id = workspace_id

    def to_clause(self, model: type[T]) -> ColumnElement[bool]:
        column = getattr(model, "workspace_id", None)
        if column is None:
            raise TypeError(f"{model.__name__} is not tenant-owned (missing workspace_id)")
        return column == self.workspace_id


class NotDeletedSpec(Specification[T]):
    """Filter soft-deleted rows out."""

    def to_clause(self, model: type[T]) -> ColumnElement[bool]:
        column = getattr(model, "deleted_at", None)
        if column is None:
            return true()
        return column.is_(None)
