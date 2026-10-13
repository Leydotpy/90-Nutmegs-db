# Runtime dependencies

SF-03 inventory and verification, 2026-10-11. `pyproject.toml` owns direct
requirements and installation profiles; `uv.lock` owns exact versions, artifact
hashes and the immutable Git source. This document does not replace the
[implementation ledger](../SANFOOTBALL_IMPLEMENTATION_STATUS.md).

## Runtime matrix

The exercised deployment target is **CPython 3.14.8 on Linux x86_64**. The project
retains its `>=3.14` Python requirement, but newer interpreters, other CPU
architectures and non-Linux production deployments have not been validated.
Gunicorn requires a Unix-like runtime. Development users on other platforms
can use Django's development server; that does not establish worker compatibility.

| Profile | Locked installation | Purpose and external requirements |
|---|---|---|
| Web, ordinary worker, scheduler, administrative jobs | `uv sync --locked --no-dev` | Django 5.2.17, DRF 3.18.0, Celery 5.6.3, Gunicorn 26.2.0. Production PostgreSQL/Redis and existing provider settings remain required. No scientific or transcription SDKs. |
| Current audio/media pipeline | `uv sync --locked --no-dev --extra media-workers` | Compatibility alias for `transcription-workers`; current audio processing calls managed transcription in the same job. FFmpeg/ffprobe executable and bounded temporary scratch space are separate system requirements. |
| Managed transcription | `uv sync --locked --no-dev --extra transcription-workers` | Google Cloud Speech 2.40.0, Google Cloud Storage 3.13.1 and OpenAI 3.5.0; credentials and provider connectivity only when invoked. This install profile does not introduce a new domain task. |
| Recommendation training | `uv sync --locked --no-dev --extra recommendation-workers` | NumPy 2.5.2, Pandas 3.0.5, SciPy 1.18.1, scikit-learn 1.9.0, FAISS CPU 1.15.0, joblib 1.5.3. Separate CPU/memory budget; no GPU or local language-model stack. |
| Development/test | `uv sync --locked --extra dev` | Coverage, Ruff, mypy, stubs and pip-audit. Worker extras are optional and can be combined explicitly for compatibility verification. |

Use a separate image or virtual environment per deployed profile. `uv sync`
reconciles installed extras, so changing profiles in one environment can remove
the previous profile's packages. Do not run it against an active worker's
environment. All profiles retain `pycflare[storages,media]` from Git commit
`f214c80de3843d47f0593386a60169c77e8bc801`.

## Inventory and cleanup decisions

The current inventory has **28 direct core requirements and 142 locked packages**
including the root project and every optional group/platform branch. Counts are
not installed sizes. The Linux web plus development environment contains 112
distributions; the combined transcription/recommendation/development environment
contains 140. Scientific/provider imports remain lazy or worker-owned.

| Dependency family | Repository owner/caller and decision |
|---|---|
| Django, DRF, filters, Guardian, CORS, Clerk SDK | Settings/app registration, `api/rest/authentication.py`, API views and permissions. Retain public identity and authorization behavior. |
| Celery, Redis, django-redis, beat/results | Existing task registration, cache, broker and scheduler; retained. |
| psycopg, dj-database-url, python-decouple | Canonical database and environment configuration; retained. |
| HTTPX, requests | `apps/promotions/client.py` and legacy offline webhook; retained. |
| Boto3, cryptography, Channels/Channels Redis | Live storage/offline delivery, encryption and channel-layer callers; retained pending their owning domain concerns. |
| Pillow, ffmpeg-python, Prometheus client | Existing image/audio utilities and transcription metrics. The small Python FFmpeg binding remains core because compatibility modules import it; FFmpeg executables and CPU work belong to media workers. |
| Babel, spectacular/sidecar | Currency/time formatting and schema/documentation; retained. |
| pycflare | Existing Cloudflare infrastructure adapter and Django storage backend; Git source/extras unchanged. |
| Gunicorn | Added maintained MIT-licensed production WSGI server; no suitable production server was declared. Locked 26.2.0 is a small pure-Python package and passed the dependency audit. |
| Clerk backend API and PyYAML | Removed redundant direct declarations: no application import; the Clerk SDK and schema/dependency graph still install their required versions. |
| gevent, honcho, python-multipart | Removed: no imports, configured pool/server or launcher callers. Workers use Celery prefork; Django/DRF owns request parsing. |
| Torch, whisper-openai | Removed obsolete optional declarations: no application imports or supported local-Whisper path. This also removes unused CUDA, transformers and related packages from the lock. Managed providers remain. |
| TensorFlow, tensorflow-datasets, QuixStreams | Unlisted legacy modules have no supported deployment profile. They are not added speculatively; legacy framework/recommendation/event concerns own migration or removal. |

The lock changed only the two security updates, the new Gunicorn package and
packages no longer reachable from requirements. Other retained versions,
including Django, Clerk, providers and scientific libraries, are unchanged.
The Clerk SDK still requires typing packages transitively in production; removing
those requires an upstream package change rather than overriding its metadata.

## Security and upgrade policy

PyJWT **2.13.0 → 2.15.1** and urllib3 **2.7.0 → 2.8.0** resolve the baseline
scanner's 17 advisory matches. Explicit `tool.uv.constraint-dependencies` bounds
(`pyjwt>=2.15.1,<3`, `urllib3>=2.8.0,<3`) prevent future uv resolutions from
reintroducing those vulnerable versions or silently crossing a major release.
These are resolver constraints, not a substitute for using the committed lock.

Upgrade narrowly with `uv lock --upgrade-package <name>`, inspect the lock diff,
run the applicable compatibility tests and audit all deployed profiles. The
pycflare revision is changed only through a reviewed provider dependency upgrade
with its storage/upload/private-delivery/webhook tests. Do not use an unpinned
moving Git branch or replace it with a similarly named index package.

The SF-03 web and combined worker audits both report **no known vulnerabilities**.
`pip-audit` skips the VCS pycflare entry because it cannot map that source to a
published package version. This is an explicit scanner coverage limit, not a
security attestation for the Git source or external services.

## Reproduction and evidence

From the repository root with CPython 3.14.8 available:

```sh
uv lock --check
uv sync --locked --extra dev
uv pip check
uv run --locked python app/manage.py test --settings=conf.settings.test

uv export --locked --no-dev --no-emit-project --no-editable --no-hashes \
  --output-file /tmp/90nutmegs-web-requirements.txt
uv run --locked pip-audit --requirement /tmp/90nutmegs-web-requirements.txt \
  --no-deps --disable-pip --progress-spinner off

uv export --locked --no-dev --extra transcription-workers \
  --extra recommendation-workers --no-emit-project --no-editable --no-hashes \
  --output-file /tmp/90nutmegs-worker-requirements.txt
uv run --locked pip-audit --requirement /tmp/90nutmegs-worker-requirements.txt \
  --no-deps --disable-pip --progress-spinner off
```

The export for scanning intentionally omits hashes because the scanner queries
package/version metadata without installing it. Installation uses the hashed
lock. The scanner's `--no-deps` is safe here only because `uv export` emits the
complete resolved dependency set, including transitives.

Actual SF-03 checks, all PASS:

- Offline `uv lock --check`, locked web/development sync and `uv pip check`.
- Fresh separate `/tmp/sf03-worker-venv` installed the locked transcription,
  recommendation and development extras; `uv pip check --python` passed there.
- Real optional SDK imports and synthetic OpenAI client construction; Google
  Speech request configuration. No network/provider calls or credentials used.
- Small real NumPy/Pandas operations, SciPy sparse matrix, scikit-learn NMF fit,
  FAISS nearest-neighbour indexing, and joblib serialization round trip.
- `media-workers` and `transcription-workers` exports contain identical packages.
- Both full resolved production profile audits above, and dependency diff review.

These checks establish dependency compatibility on the stated runtime, not
successful production training, transcription, provider access or load capacity.
The existing transcription helper passes a literal OpenAI API-key placeholder and
has response normalization defects; SF-15 owns these behavior fixes. Existing
recommendation data/algorithm/artifact lifecycle issues remain SF-18. No provider
request, model download, production dataset, database migration or deployment was
performed for this inventory.

Rollback dependency changes together with their process definitions, then run
`uv sync --locked` for the intended profile in a fresh environment. No schema or
data rollback is required. Restoring the old lock reintroduces the recorded
PyJWT/urllib3 advisory matches and is not a security-neutral rollback.
