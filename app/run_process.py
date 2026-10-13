"""Run one bounded process per deployment unit, passing termination signals directly."""

import argparse
import os
import shlex
import sys
from pathlib import Path

WORKER_PROFILES = {
    # queue, default concurrency, maximum resident memory per child (KiB)
    "worker-default": ("celery", 2, 512 * 1024),
    "worker-media": ("media", 1, 4 * 1024 * 1024),
    "worker-bulk": ("bulk", 1, 2 * 1024 * 1024),
}


def bounded_integer(value: str) -> int:
    try:
        result = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer from 1 to 32") from None
    if not 1 <= result <= 32:
        raise argparse.ArgumentTypeError("must be an integer from 1 to 32")
    return result


def build_command(arguments: list[str]) -> tuple[list[str], bool]:
    """Return the exact command without importing Django or launching work."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run", action="store_true", help="print the command without executing"
    )
    roles = parser.add_subparsers(dest="role", required=True)
    web = roles.add_parser("web")
    web.add_argument("--concurrency", type=bounded_integer, default=2)
    web.add_argument("--bind", default="0.0.0.0:8000")
    for role in WORKER_PROFILES:
        worker = roles.add_parser(role)
        worker.add_argument("--concurrency", type=bounded_integer)
    roles.add_parser("scheduler")
    admin = roles.add_parser("admin")
    admin.add_argument("management_arguments", nargs=argparse.REMAINDER)
    options = parser.parse_args(arguments)
    if options.role == "web":
        command = [
            sys.executable,
            "-m",
            "gunicorn",
            "conf.wsgi:application",
            "--bind",
            options.bind,
            "--workers",
            str(options.concurrency),
            "--worker-class",
            "sync",
            "--timeout",
            "60",
            "--graceful-timeout",
            "30",
            "--max-requests",
            "1000",
            "--max-requests-jitter",
            "100",
            "--logger-class",
            "conf.gunicorn_logging.RedactingLogger",
            "--error-logfile",
            "-",
        ]
    elif options.role in WORKER_PROFILES:
        queue, concurrency, memory = WORKER_PROFILES[options.role]
        command = [
            sys.executable,
            "-m",
            "celery",
            "-A",
            "conf",
            "worker",
            "--hostname",
            f"{options.role}@%h",
            "--queues",
            queue,
            "--pool",
            "prefork",
            "--concurrency",
            str(options.concurrency or concurrency),
            "--prefetch-multiplier",
            "1",
            "--soft-time-limit",
            "1740",
            "--time-limit",
            "1800",
            "--max-tasks-per-child",
            "100",
            "--max-memory-per-child",
            str(memory),
            "--loglevel",
            "INFO",
        ]
    elif options.role == "scheduler":
        command = [
            sys.executable,
            "-m",
            "celery",
            "-A",
            "conf",
            "beat",
            "--scheduler",
            "django_celery_beat.schedulers:DatabaseScheduler",
            "--pidfile",
            "",
            "--loglevel",
            "INFO",
        ]
    else:
        if not options.management_arguments:
            parser.error("admin requires a Django management command")
        command = [sys.executable, "manage.py", *options.management_arguments]
    return command, options.dry_run


def main() -> None:
    command, dry_run = build_command(sys.argv[1:])
    if dry_run:
        print(shlex.join(command))
        return
    os.chdir(Path(__file__).resolve().parent)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "conf.settings.production")
    os.execv(sys.executable, command)


if __name__ == "__main__":
    main()
