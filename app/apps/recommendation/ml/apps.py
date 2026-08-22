from django.apps import AppConfig


class MLRecommendationConfig(AppConfig):
    name = 'apps.recommendation.ml'
    label = 'ml'

    def ready(self):
        # Keep startup lightweight. Artifacts are loaded lazily when the
        # recommendation query path is actually used.
        return None

