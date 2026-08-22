import logging

from django.conf import settings

try:
    import quixstreams.Application as Application
except ImportError:
    Application = None

KAFKA_BROKER_ADDRESS = getattr(settings, 'KAFKA_BROKER_ADDRESS', "localhost:9092")
DEBUG = getattr(settings, 'DEBUG', True)


def publish(key: str, msg: str):
    app = Application(
        broker_address=KAFKA_BROKER_ADDRESS,
        loglevel="DEBUG" if DEBUG else "INFO",
    )

    with app.get_producer() as producer:
        producer.produce(
            topic="auth.events",
            key=key,
            value=msg,
        )
        logging.info(f"Message {key} produced")
