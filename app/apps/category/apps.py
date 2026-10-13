from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CategoryConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.category"
    label = "category"
    verbose_name = _("Category")
    verbose_name_plural = _("Categories")
