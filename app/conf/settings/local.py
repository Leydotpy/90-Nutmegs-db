"""Deprecated alias for :mod:`conf.settings.development`.

This module remains temporarily for developers with an existing explicit
``conf.settings.local`` command. It no longer participates in settings
selection by file existence.
"""

from .development import *  # noqa: F401,F403

