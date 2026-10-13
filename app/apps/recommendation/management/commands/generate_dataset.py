from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = "Export recommendation datasets to the configured output directory."

    def handle(self, *args, **options):
        try:
            from core.recommender.datasets.builder import load_from_db_as_dfs
        except ImportError:
            raise CommandError(
                "Dataset export requires the recommendation-workers dependency extra"
            ) from None
        output_dir = Path(settings.RECOMMENDER_OUTPUT_PATH)
        output_dir.mkdir(parents=True, exist_ok=True)

        attributes_df, interactions_df, popularity_df = load_from_db_as_dfs()

        files = {
            "attributes": output_dir / "podcast_attributes.csv",
            "interactions": output_dir / "podcast_interactions.csv",
            "popularity": output_dir / "podcast_popularity.csv",
        }

        attributes_df.to_csv(files["attributes"], index=False)
        interactions_df.to_csv(files["interactions"], index=False)
        popularity_df.to_csv(files["popularity"], index=False)

        manifest = {
            "dataset_version": 1,
            "generated_at": timezone.now().isoformat(),
            "files": {name: path.name for name, path in files.items()},
            "rows": {
                "attributes": int(len(attributes_df)),
                "interactions": int(len(interactions_df)),
                "popularity": int(len(popularity_df)),
            },
        }
        (output_dir / "dataset_manifest.json").write_text(
            json.dumps(manifest, indent=2),
            encoding="utf-8",
        )

        self.stdout.write(self.style.SUCCESS(f"Exported recommendation datasets to {output_dir}"))
