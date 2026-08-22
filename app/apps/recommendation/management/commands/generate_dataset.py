from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.recommender.datasets.builder import load_from_db_as_dfs


class Command(BaseCommand):
    help = "Export the recommendation datasets from the main app into the shared microservice directory."

    def handle(self, *args, **options):
        output_dir = Path(getattr(settings, "RECOMMENDER_OUTPUT_PATH"))
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

        self.stdout.write(
            self.style.SUCCESS(
                f"Exported recommendation datasets to {output_dir}"
            )
        )
