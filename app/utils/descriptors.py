

class _ClassProperty:
    """Descriptor to create a read-only property on the class (accessible as Class.attr)."""

    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner=None):
        if owner is None:
            owner = type(instance)
        return self.func(owner)


classproperty = _ClassProperty

__all__ = ['classproperty']