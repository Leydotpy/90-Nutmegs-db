"""Project-aware Django test discovery."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any
from unittest import TestSuite

from django.conf import settings
from django.test.runner import DiscoverRunner


class SourceRootDiscoverRunner(DiscoverRunner):
    """Discover tests beneath Django's source root when no labels are given.

    ``manage.py`` lives in ``app/`` but is normally invoked from the repository
    root. Django otherwise starts discovery at the current working directory,
    whose non-package ``app`` directory prevents ``unittest`` from descending
    into the actual ``api``, ``apps``, and ``conf`` packages.
    """

    def build_suite(
        self,
        test_labels: Sequence[str] | None = None,
        **kwargs: Any,
    ) -> TestSuite:
        using_default_root = not test_labels
        source_root = str(settings.BASE_DIR)
        labels = list(test_labels) if test_labels else [source_root]
        configured_top_level = self.top_level
        if using_default_root and configured_top_level is None:
            self.top_level = source_root
        try:
            suite = super().build_suite(labels, **kwargs)
        finally:
            self.top_level = configured_top_level

        unfiltered_default = (
            not self.tags
            and not self.exclude_tags
            and not self.test_name_patterns
            and self.pattern == "test*.py"
        )
        if using_default_root and unfiltered_default and suite.countTestCases() == 0:
            raise RuntimeError(
                f"Default test discovery found no tests beneath {settings.BASE_DIR}."
            )
        return suite
