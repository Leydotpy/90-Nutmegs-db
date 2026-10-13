from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RecommendationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.recommendation"
    label = "recommendation"
    verbose_name = _("Recommendation")
    verbose_name_plural = _("Recommendations")
