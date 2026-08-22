from dataclasses import dataclass, field, Field
from typing import Callable, Dict, Optional, Type, Any

from django.db.models import QuerySet
from rest_framework import serializers


@dataclass(frozen=True)
class ResourceConfig:
    """
    Declarative configuration for a child resource.
    - serializer: DRF serializer class
    - queryset_factory: callable that accepts the view instance and returns a QuerySet
    - scope_field: optional FK field name used to scope by parent id (e.g. "region_id")
    """
    serializer: Type[serializers.BaseSerializer]
    queryset_factory: Callable[[Any], QuerySet]
    scope_field: Optional[str] = None


class ResourceRegistry:
    """Module-level registry that supports decorator-style registration."""

    def __init__(self) -> None:
        self._map: Dict[str, ResourceConfig] = {}

    def register_direct(self, key: str, config: ResourceConfig) -> None:
        if key in self._map:
            raise KeyError(f"Resource key already registered: {key!r}")
        self._map[key] = config

    def register(self, key: str, *, overwrite: bool = False):
        """
        Decorator factory. Can decorate:
          - a zero-arg function returning ResourceConfig, or
          - a callable (class) that returns ResourceConfig when invoked.
        The decorator returns the original object (so imports behave naturally).
        """

        def _decorator(factory_or_config):
            # support direct ResourceConfig being passed accidentally
            if isinstance(factory_or_config, ResourceConfig):
                cfg = factory_or_config
            else:
                # call if callable (function or class) to get ResourceConfig
                if not callable(factory_or_config):
                    raise TypeError("Decorator must wrap a callable that returns ResourceConfig")
                cfg = factory_or_config()
            if not isinstance(cfg, ResourceConfig):
                raise TypeError("Factory must return a ResourceConfig instance")
            if key in self._map and not overwrite:
                raise KeyError(f"Resource key already registered: {key!r}")
            self._map[key] = cfg
            return factory_or_config  # return original object so decorator is non-intrusive

        return _decorator

    def get(self, key: str) -> Optional[ResourceConfig]:
        return self._map.get(key)

    def keys(self):
        return tuple(self._map.keys())
