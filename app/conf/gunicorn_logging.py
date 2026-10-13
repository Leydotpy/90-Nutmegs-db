"""Apply the canonical secret redactor to Gunicorn's own error handlers."""

from gunicorn.glogging import Logger

from conf.logging import RedactingFormatter


class RedactingLogger(Logger):
    def setup(self, cfg) -> None:
        super().setup(cfg)
        for logger in (self.error_log, self.access_log):
            for handler in logger.handlers:
                handler.setFormatter(RedactingFormatter("%(levelname)s %(name)s %(message)s"))
