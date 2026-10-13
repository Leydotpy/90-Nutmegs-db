"""Exercise the configured redactor through real logging handlers."""

from __future__ import annotations

import io
import json
import logging
import sys
from urllib.parse import quote, quote_plus

from django.test import SimpleTestCase, override_settings

from conf.logging import REDACTED, RedactingFormatter


class RedactingFormatterTests(SimpleTestCase):
    def setUp(self):
        self.output = io.StringIO()
        self.handler = logging.StreamHandler(self.output)
        self.handler.setFormatter(RedactingFormatter("%(levelname)s %(name)s %(message)s"))
        self.logger = logging.Logger("sf02.redaction", level=logging.INFO)
        self.logger.addHandler(self.handler)
        self.addCleanup(self.handler.close)

    def test_plain_operational_metadata_is_preserved(self):
        self.logger.info(
            "upload completed episode_id=%s provider=r2 duration_ms=12 key_length=256 "
            "signing_key_id=public-id retries=0 url=https://media.example.test/image.jpg",
            "episode-123",
        )
        self.assertEqual(
            self.output.getvalue(),
            "INFO sf02.redaction upload completed episode_id=episode-123 provider=r2 "
            "duration_ms=12 key_length=256 signing_key_id=public-id retries=0 "
            "url=https://media.example.test/image.jpg\n",
        )

    @override_settings(CLERK_SECRET_KEY="synthetic-configured-clerk-credential")
    def test_configured_values_are_redacted_in_messages_arguments_and_extra(self):
        secret = "synthetic-configured-clerk-credential"
        self.handler.setFormatter(RedactingFormatter("%(message)s context=%(context)s"))
        self.logger.info(f"provider rejected {secret}: %s", secret, extra={"context": secret})
        self.assertNotIn(secret, self.output.getvalue())
        self.assertEqual(self.output.getvalue().count(REDACTED), 3)

    def test_rotation_uses_current_canonical_settings(self):
        with override_settings(OPENAI_API_KEY="synthetic-initial-key"):
            self.logger.info("provider rejected %s", "synthetic-initial-key")
        with override_settings(OPENAI_API_KEY="synthetic-rotated-key"):
            self.logger.info("provider rejected %s", "synthetic-rotated-key")
        self.assertNotIn("synthetic-initial-key", self.output.getvalue())
        self.assertNotIn("synthetic-rotated-key", self.output.getvalue())
        self.assertEqual(self.output.getvalue().count(REDACTED), 2)

    def test_configured_values_in_repr_json_url_encoding_and_newlines(self):
        secret = "synthetic value/'\"\\\nnext-line"
        with override_settings(GIFFY_SHARED_SECRET=secret):
            for value in (
                secret,
                repr(secret),
                json.dumps(secret),
                quote(secret),
                quote_plus(secret),
            ):
                with self.subTest(representation=value[:9]):
                    self.output.seek(0)
                    self.output.truncate()
                    self.logger.info("provider rejected %s", value)
                    self.assertNotIn("synthetic", self.output.getvalue())
                    self.assertNotIn("next-line", self.output.getvalue())

    @override_settings(
        DATABASES={"default": {"PASSWORD": "synthetic-db-password"}},
        CACHES={"default": {"LOCATION": "redis://:synthetic-cache-password@localhost/1"}},
        SECRET_KEY_FALLBACKS=["synthetic-old-signing-key"],
    )
    def test_nested_backend_credentials_and_fallback_keys(self):
        self.logger.info(
            "backend error: %s %s %s",
            "synthetic-db-password",
            "synthetic-cache-password",
            "synthetic-old-signing-key",
        )
        self.assertNotIn("synthetic-", self.output.getvalue())
        self.assertEqual(self.output.getvalue().count(REDACTED), 3)

    def test_structured_args_mask_sensitive_values_and_keep_identifiers(self):
        self.logger.info(
            "delivery failed %r",
            {
                "episode_id": "episode-123",
                "password": "synthetic unknown password",
                "nested": {
                    "api_key": "synthetic-api-key",
                    "access_token": "synthetic-access-token",
                    "private_key": "synthetic-private-key",
                    "refreshToken": "synthetic-refresh-token",
                },
            },
        )
        rendered = self.output.getvalue()
        self.assertNotIn("synthetic", rendered)
        self.assertIn("episode-123", rendered)
        self.assertEqual(rendered.count(REDACTED), 5)

    def test_headers_and_unlabelled_basic_bearer_credentials(self):
        self.logger.info(
            "request %s %r",
            "Bearer synthetic-bearer-value Basic c3ludGhldGljOmNyZWRlbnRpYWw=",
            {
                "Authorization": "Bearer synthetic-header-value",
                "Cookie": "session=synthetic-cookie",
            },
        )
        rendered = self.output.getvalue()
        self.assertNotIn("synthetic", rendered)
        self.assertNotIn("c3ludGhldGlj", rendered)
        self.assertIn("request", rendered)

    def test_signed_and_credential_urls_are_removed(self):
        for url in (
            "https://media.example.test/audio.mp3?X-Amz-Signature=synthetic-sig&expires=123",
            "https://media.example.test/image.jpg?token=synthetic-image-token",
            "https://media.example.test/image.jpg?accessToken=synthetic-image-token",
            "https://media.example.test/audio.mp3?sig=synthetic-sig",
            "https://media.example.test/audio.mp3?Policy=synthetic-policy&Key-Pair-Id=public-id",
            "https://stream.example.test/eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIxIn0.signature/manifest/video.m3u8",
            "https://upload.videodelivery.net/synthetic-upload-capability",
            "https://upload.imagedelivery.net/synthetic-image-capability",
            "postgresql://operator:synthetic-db-password@db.example.test/database",
            "rediss://:synthetic-cache-password@cache.example.test/1",
            "https://operator:synthetic-password@[invalid-host]/",
        ):
            with self.subTest(kind=url.split(":", 1)[0]):
                self.output.seek(0)
                self.output.truncate()
                self.logger.warning("provider failed for %s", url)
                self.assertEqual(
                    self.output.getvalue(),
                    f"WARNING sf02.redaction provider failed for {REDACTED}\n",
                )

    def test_unknown_private_key_pem_is_removed_even_in_repr(self):
        private_key = (
            "-----BEGIN RSA PRIVATE KEY-----\nsynthetic-key-material\n-----END RSA PRIVATE KEY-----"
        )
        for value in (private_key, repr(private_key)):
            self.logger.warning("signing failed: %s", value)
        self.assertNotIn("PRIVATE KEY", self.output.getvalue())
        self.assertNotIn("synthetic-key-material", self.output.getvalue())
        self.assertEqual(self.output.getvalue().count(REDACTED), 2)

    def test_whole_webhook_payload_is_removed_including_nested_repr(self):
        payload = {
            "customer": {"email": "synthetic@example.test", "card": {"last4": "1234"}},
            "items": [1, 2],
        }
        for label in ("webhook_payload", "webhook payload", "webhook_body"):
            self.logger.warning("event_id=evt-123 %s=%r outcome=rejected", label, payload)
        rendered = self.output.getvalue()
        self.assertNotIn("synthetic@example.test", rendered)
        self.assertNotIn("1234", rendered)
        self.assertEqual(rendered.count("event_id=evt-123"), 3)
        self.assertEqual(rendered.count("outcome=rejected"), 3)

    def test_quoted_escaped_and_unclosed_values_fail_closed(self):
        for message in (
            'password="synthetic white space" event_id=evt-123',
            r"password='synthetic \'quoted\' value' event_id=evt-123",
            "password=synthetic white space event_id=evt-123",
            "password='synthetic unfinished\nsecond-line",
            'webhook_payload={"email": "synthetic@example.test"',
        ):
            self.output.seek(0)
            self.output.truncate()
            self.logger.warning(message)
            self.assertNotIn("synthetic", self.output.getvalue())
            self.assertNotIn("second-line", self.output.getvalue())
            if "event_id" in message:
                self.assertIn("event_id=evt-123", self.output.getvalue())

    @override_settings(CLOUDFLARE_API_TOKEN="synthetic-exception-secret")
    def test_exception_chain_and_stack_are_redacted(self):
        try:
            try:
                raise ValueError("upstream rejected synthetic-exception-secret")
            except ValueError as error:
                raise RuntimeError("password='synthetic exception password'") from error
        except RuntimeError:
            self.logger.exception("provider operation failed", stack_info=True)
        rendered = self.output.getvalue()
        self.assertIn("Traceback", rendered)
        self.assertIn("ValueError", rendered)
        self.assertIn("RuntimeError", rendered)
        self.assertIn("Stack", rendered)
        self.assertNotIn("synthetic-exception-secret", rendered)
        self.assertNotIn("synthetic exception password", rendered)

    def test_shared_record_and_cached_exception_text_are_not_mutated(self):
        try:
            raise ValueError("password='synthetic-cached-exception-secret'")
        except ValueError:
            record = self.logger.makeRecord(
                self.logger.name,
                logging.ERROR,
                __file__,
                1,
                "provider failed %r",
                ({"token": "synthetic-record-token"},),
                sys.exc_info(),
            )
        # A prior handler can have cached sensitive traceback output already.
        record.exc_text = logging.Formatter().formatException(record.exc_info)
        record.stack_info = "Stack metadata: password='synthetic-stack-secret'"
        original = record.__dict__.copy()
        self.handler.handle(record)
        self.assertEqual(record.__dict__, original)
        self.assertNotIn("synthetic-", self.output.getvalue())
        self.assertIn("synthetic-record-token", logging.Formatter().format(record))
