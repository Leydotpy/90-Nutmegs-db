"""Settings package with an isolated, deprecated direct compatibility alias.

New entry points must select one explicit module with ``DJANGO_SETTINGS_MODULE``:

* ``conf.settings.development`` for local development;
* ``conf.settings.test`` for automated tests;
* ``conf.settings.production`` for deployed environments.

Historically ``conf.settings`` selected configuration by checking whether a
committed ``local.py`` existed. The development shim is now activated only when
``DJANGO_SETTINGS_MODULE`` is exactly ``conf.settings``. Importing an explicit
child such as ``conf.settings.production`` leaves this package side-effect-free.
"""

import os
import warnings

if os.environ.get("DJANGO_SETTINGS_MODULE") == __name__:
    warnings.warn(
        "conf.settings is a deprecated development-only compatibility module; "
        "set DJANGO_SETTINGS_MODULE explicitly",
        DeprecationWarning,
        stacklevel=2,
    )
    from .development import *  # noqa: F401,F403,E402
