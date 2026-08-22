# pylint: disable=W0212, W0201, W0632
import logging
import operator
from os.path import basename, join
from urllib.error import HTTPError
from urllib.parse import urlsplit, parse_qs

from django.conf import settings as django_settings
from django.core.files import File
from django.db import IntegrityError
from django.utils.functional import cached_property
from rest_framework import serializers, relations
from rest_framework.fields import get_attribute

from api.rest.utils import settings
from api.rest.utils.exists import bound_unique_together_get_or_create
from api.rest.utils.loading import get_api_class

logger = logging.getLogger(__name__)


class TagsField(serializers.Field):
    """
    DRF field for CommaSeparatedCharField.
    Converts between DB string ("foo,bar,baz") and Python list internally.
    Can render as either a list or a comma-delimited string in API responses.
    """

    def __init__(self, *args, render_as_list=True, **kwargs):
        """
        :param render_as_list: If True, return a list in API output.
                               If False, return a comma-delimited string.
        """
        self.render_as_list = render_as_list
        super().__init__(*args, **kwargs)

    def to_representation(self, value):
        """
        Convert model field value into API output.
        """
        if value is None:
            return [] if self.render_as_list else ""

        # Normalize into list first
        if isinstance(value, list):
            items = [str(v).strip() for v in value if str(v).strip()]
        else:
            items = [v.strip() for v in str(value).split(',') if v.strip()]

        # Render based on option
        if self.render_as_list:
            return items
        return ",".join(items)

    def to_internal_value(self, data):
        """
        Convert incoming API data into Python list for the model.
        Accepts either a list or a comma-delimited string.
        """
        if isinstance(data, list):
            return [str(v).strip() for v in data if str(v).strip()]
        if isinstance(data, str):
            return [v.strip() for v in data.split(',') if v.strip()]
        raise serializers.ValidationError("Expected a list of strings or a comma-separated string.")
