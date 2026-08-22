import json
import logging
import threading

from django.conf import settings

try:
    import quixstreams.Application as Application
except ImportError:
    Application = None


KAFKA_BROKER_ADDRESS = getattr(settings, 'KAFKA_BROKER_ADDRESS', "localhost:9092")
KAFKA_AUTH_TOPICS = getattr(settings, 'KAFKA_AUTH_TOPICS', [])
DEBUG = getattr(settings, 'DEBUG', True)


def _consume(*topics):

    app = Application(
        broker_address=KAFKA_BROKER_ADDRESS,
        loglevel="DEBUG" if DEBUG else 'INFO',
        consumer_group="auth-consumer",
        auto_offset_reset="latest",
    )

    with app.get_consumer() as consumer:
        consumer.subscribe(list(topics))

        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                print("waiting...")
            elif msg.error() is not None:
                raise ValueError(msg.error())
            else:
                key = msg.key().decode('utf-8')
                value = json.loads(msg.value())
                offset = msg.offset()

                print("Received message '{}' on topic '{}' with {} offset".format(key, value, offset))
                consumer.store_offsets(msg) # noqa


def consume():
    thread = threading.Thread(target=_consume, args=KAFKA_AUTH_TOPICS, daemon=True)
    thread.start()


__all__ = ['consume']