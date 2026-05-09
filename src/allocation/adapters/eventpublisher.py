import json
import logging
from dataclasses import asdict
import redis
import abc
from allocation import config
from allocation.domain import events

logger = logging.getLogger(__name__)


class Publisher(abc.ABC):

    @abc.abstractmethod
    def publish(self, *args, **kwargs):
        ...


DEFAULT_REDIS_CONFIG = config.get_redis_host_and_port()

class RedisPublisher(Publisher):

    def __init__(self, redis_config=DEFAULT_REDIS_CONFIG):
        self.r = redis.Redis(**redis_config)

    def publish(self, channel, event: events.Event):
        logging.debug("publish: channgel=%s, event=%s", channel, event)
        self.r.publish(channel, json.dumps(asdict(event)))
