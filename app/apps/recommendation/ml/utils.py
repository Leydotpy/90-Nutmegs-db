from __future__ import annotations

from pathlib import Path
from typing import Any

import joblib
import numpy as np
from django.conf import settings

ARTIFACT_DIR = Path(getattr(settings, "RECOMMENDER_ARTIFACT_DIR"))

_ARTIFACT_CACHE: dict[str, Any] | None = None


def artifact_path(name: str) -> Path:
    return ARTIFACT_DIR / name


def artifacts_available() -> bool:
    required = (
        "nmf_model.joblib",
        "nmf_meta.joblib",
        "W.npy",
        "H.npy",
        "tfidf.joblib",
        "svd.joblib",
        "content_meta.joblib",
        "X_svd.npy",
        "faiss_index.ivf",
        "hybrid_meta.joblib",
    )
    return all(artifact_path(filename).exists() for filename in required)


def load_nmf():
    return (
        joblib.load(artifact_path("nmf_model.joblib")),
        joblib.load(artifact_path("nmf_meta.joblib")),
        np.load(artifact_path("W.npy")),
        np.load(artifact_path("H.npy")),
    )


def load_content():
    return (
        joblib.load(artifact_path("tfidf.joblib")),
        joblib.load(artifact_path("svd.joblib")),
        joblib.load(artifact_path("content_meta.joblib")),
        np.load(artifact_path("X_svd.npy")),
    )


def load_faiss_index():
    import faiss

    return (
        faiss.read_index(str(artifact_path("faiss_index.ivf"))),
        joblib.load(artifact_path("hybrid_meta.joblib")),
    )


def load_all_artifacts(force_reload: bool = False) -> dict[str, Any]:
    global _ARTIFACT_CACHE

    if _ARTIFACT_CACHE is not None and not force_reload:
        return _ARTIFACT_CACHE

    if not artifacts_available():
        missing = [
            path.name
            for path in (artifact_path(name) for name in (
                "nmf_model.joblib",
                "nmf_meta.joblib",
                "W.npy",
                "H.npy",
                "tfidf.joblib",
                "svd.joblib",
                "content_meta.joblib",
                "X_svd.npy",
                "faiss_index.ivf",
                "hybrid_meta.joblib",
            ))
            if not path.exists()
        ]
        raise FileNotFoundError(
            f"Recommendation artifacts are missing from {ARTIFACT_DIR}: {', '.join(missing)}"
        )

    nmf, nmf_meta, W, H = load_nmf()
    tf, svd, content_meta, X_svd = load_content()
    faiss_index, hybrid_meta = load_faiss_index()

    hybrid_matrix = None
    hybrid_file = artifact_path("hybrid.npy")
    if hybrid_file.exists():
        hybrid_matrix = np.load(hybrid_file)

    _ARTIFACT_CACHE = {
        "nmf": nmf,
        "nmf_meta": nmf_meta,
        "W": W,
        "H": H,
        "tf": tf,
        "svd": svd,
        "content_meta": content_meta,
        "X_svd": X_svd,
        "faiss_index": faiss_index,
        "hybrid_meta": hybrid_meta,
        "hybrid_matrix": hybrid_matrix,
    }
    return _ARTIFACT_CACHE


def get_user_vector_ann(user_id, user_to_index, W, hybrid_item_matrix):
    if user_id not in user_to_index:
        return None

    uidx = user_to_index[user_id]
    vec_nmf = W[uidx]
    content_part = np.zeros(max(hybrid_item_matrix.shape[1] - vec_nmf.shape[0], 0), dtype="float32")
    vec = np.concatenate([vec_nmf.astype("float32"), content_part]).reshape(1, -1)
    norm = np.linalg.norm(vec)
    if norm == 0:
        return None
    return (vec / norm).astype("float32")
