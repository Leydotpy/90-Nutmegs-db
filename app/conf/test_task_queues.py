"""SF-03 broker routing, scheduler registration and process lifecycle contracts."""

import contextlib
import io
import os
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock
from urllib.request import urlopen

from celery import Celery
from django.conf import settings
from django.core.management import get_commands
from run_process import build_command

from conf.celery import app
from conf.task_queues import BEAT_SCHEDULE, TASK_QUEUES, TASK_ROUTES
from conf.tasks import collect_orphaned_packages, expire_offline_licenses, revoke_inactive_devices

APP_DIRECTORY = Path(__file__).resolve().parents[1]


class QueueContractTests(unittest.TestCase):
    def test_existing_task_identities_route_to_independent_pools_over_memory_transport(self):
        isolated = Celery("sf03-route-contract", broker="memory://")
        isolated.conf.update(
            task_queues=TASK_QUEUES,
            task_routes=TASK_ROUTES,
            task_default_queue="celery",
            task_create_missing_queues=False,
        )
        with isolated.connection_for_write() as connection:
            for name, destination in TASK_ROUTES.items():
                with self.subTest(name=name):
                    isolated.send_task(name, connection=connection)
                    queue = connection.SimpleQueue(destination["queue"])
                    message = queue.get(block=False)
                    self.assertEqual(message.headers["task"], name)
                    message.ack()
                    queue.close()
        isolated.close()

    def test_every_scheduled_target_is_registered_and_has_a_route(self):
        app.loader.import_default_modules()
        for entry in settings.CELERY_BEAT_SCHEDULE.values():
            self.assertIn(entry["task"], app.tasks)
            self.assertIn(entry["task"], TASK_ROUTES)
            self.assertNotIn("args", entry)
        self.assertNotIn("django.core.management.call_command", app.tasks)
        self.assertEqual(settings.CELERY_IMPORTS, ("conf.tasks",))

    def test_interval_cadence_is_preserved(self):
        self.assertEqual(
            set(BEAT_SCHEDULE),
            {
                "recalc-user-category-affinity-every-10-min",
                "expire-licenses-daily",
                "rotate-cloud-front-cookies",
                "revoke-inactive-devices-weekly",
                "gc-orphan-packages-daily",
            },
        )
        self.assertEqual(
            sorted(entry["schedule"] for entry in BEAT_SCHEDULE.values()),
            [86400, 86400, 86400, 86400, 604800],
        )

    def test_scheduler_wrappers_only_invoke_the_intended_registered_commands(self):
        cases = (
            (expire_offline_licenses, "expire_licenses", {}),
            (revoke_inactive_devices, "revoke_inactive_licenses", {"days": 90}),
            (collect_orphaned_packages, "gc_orphaned_packages", {"days": 30}),
        )
        for task, command, kwargs in cases:
            with self.subTest(command=command), mock.patch("conf.tasks.call_command") as invoke:
                self.assertIn(command, get_commands())
                task.run()
                invoke.assert_called_once_with(command, **kwargs)
                with self.assertRaises(TypeError):
                    task.run("untrusted_command")


class ProcessContractTests(unittest.TestCase):
    def test_processes_use_distinct_queues_without_embedded_beat(self):
        for role, queue in (
            ("worker-default", "celery"),
            ("worker-media", "media"),
            ("worker-bulk", "bulk"),
        ):
            with self.subTest(role=role):
                command, _ = build_command([role])
                self.assertEqual(command[command.index("--queues") + 1], queue)
                self.assertEqual(command[command.index("--prefetch-multiplier") + 1], "1")
                self.assertNotIn("--beat", command)
                self.assertIn("--time-limit", command)
                self.assertIn("--max-memory-per-child", command)
        scheduler, _ = build_command(["scheduler"])
        self.assertIn("django_celery_beat.schedulers:DatabaseScheduler", scheduler)

    def test_invalid_or_unbounded_concurrency_is_rejected(self):
        for value in ("0", "-1", "33", "not-an-integer"):
            with (
                self.subTest(value=value),
                contextlib.redirect_stderr(io.StringIO()),
                self.assertRaises(SystemExit) as raised,
            ):
                build_command(["worker-media", "--concurrency", value])
            self.assertEqual(raised.exception.code, 2)

    def test_admin_requires_an_explicit_management_command(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            build_command(["admin"])
        command, _ = build_command(["admin", "check", "--deploy"])
        self.assertEqual(command[-3:], ["manage.py", "check", "--deploy"])

    def test_gunicorn_errors_use_the_canonical_secret_redactor(self):
        from gunicorn.config import Config

        from conf.gunicorn_logging import RedactingLogger

        logger = RedactingLogger(Config())
        stream = io.StringIO()
        handler = logger.error_log.handlers[0]
        previous_stream = handler.stream
        handler.setStream(stream)
        try:
            logger.error("Synthetic failure containing %s", settings.GIFFY_SHARED_SECRET)
        finally:
            handler.setStream(previous_stream)
        self.assertIn("[REDACTED]", stream.getvalue())
        self.assertNotIn(settings.GIFFY_SHARED_SECRET, stream.getvalue())

    def test_dry_run_requires_no_production_secrets_and_runs_no_process(self):
        environment = {"PATH": os.environ["PATH"]}
        result = subprocess.run(
            [sys.executable, str(APP_DIRECTORY / "run_process.py"), "--dry-run", "worker-media"],
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        self.assertIn("--queues media", result.stdout)
        self.assertEqual(result.stderr, "")

    def _start_process(self, role, *arguments):
        output = self.enterContext(tempfile.TemporaryFile(mode="w+"))
        environment = {**os.environ, "DJANGO_SETTINGS_MODULE": "conf.settings.test"}
        process = subprocess.Popen(
            [sys.executable, str(APP_DIRECTORY / "run_process.py"), role, *arguments],
            cwd=APP_DIRECTORY.parent,
            env=environment,
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )

        def cleanup():
            if process.poll() is None:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=5)

        self.addCleanup(cleanup)
        return process, output

    def test_idle_worker_starts_on_memory_broker_and_handles_term(self):
        process, output = self._start_process("worker-default", "--concurrency", "1")
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            output.seek(0)
            captured = output.read()
            if " ready." in captured or process.poll() is not None:
                break
            time.sleep(0.05)
        self.assertIsNone(process.poll(), captured)
        self.assertIn(" ready.", captured)
        process.terminate()
        self.assertEqual(process.wait(timeout=15), 0)
        output.seek(0)
        self.assertIn("Warm shutdown", output.read())

    def test_web_serves_liveness_and_readiness_and_handles_term(self):
        with socket.socket() as reserve:
            reserve.bind(("127.0.0.1", 0))
            port = reserve.getsockname()[1]
        process, output = self._start_process(
            "web", "--bind", f"127.0.0.1:{port}", "--concurrency", "1"
        )
        deadline = time.monotonic() + 20
        response = None
        while time.monotonic() < deadline:
            try:
                with urlopen(f"http://127.0.0.1:{port}/health/live/", timeout=1) as probe:
                    response = probe.read()
                    break
            except OSError:
                if process.poll() is not None:
                    break
                time.sleep(0.05)
        output.seek(0)
        self.assertIsNotNone(response, output.read())
        self.assertIn(b'"status": "ok"', response)
        with urlopen(f"http://127.0.0.1:{port}/health/ready/", timeout=2) as probe:
            self.assertIn(b'"status": "ready"', probe.read())
        process.terminate()
        self.assertEqual(process.wait(timeout=10), 0)
