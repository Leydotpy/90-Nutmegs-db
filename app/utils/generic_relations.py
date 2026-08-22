"""Utilities for Django generic relations across mixed primary-key types."""

from __future__ import annotations

from typing import Any


def normalize_generic_object_id(value: Any) -> str:
    """Return a stable string identifier for GenericForeignKey object lookups."""
    resolved = getattr(value, "pk", value)
    if resolved is None:
        return ""
    return str(resolved)
