from rest_framework import serializers


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
            items = [v.strip() for v in str(value).split(",") if v.strip()]

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
            return [v.strip() for v in data.split(",") if v.strip()]
        raise serializers.ValidationError("Expected a list of strings or a comma-separated string.")
