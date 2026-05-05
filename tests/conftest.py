import shutil
import subprocess

import pytest

import requests
import redis
from tenacity import retry, stop_after_delay


from sqlalchemy import create_engine
from sqlalchemy.orm import clear_mappers
from src.allocation.adapters import orm
from src.allocation import config
from src.allocation.entrypoints.event_channels import ChannelEventConsumerOnline, ChannelEventConsumerPing


@pytest.fixture
def in_memory_sqlite_db():
    engine = create_engine("sqlite:///:memory:")
    orm.metadata.create_all(engine)
    return engine


@pytest.fixture
def sqlite_session_factory(in_memory_sqlite_db):
    yield orm.sessionmaker(bind=in_memory_sqlite_db)


@pytest.fixture
def sqlite_session(sqlite_session_factory):
    return sqlite_session_factory()


@pytest.fixture(scope="session")
def postgres_db():
    engine = create_engine(config.get_postgres_uri())
    wait_for_postgres_to_come_up(engine)
    orm.metadata.create_all(engine)
    return engine


@pytest.fixture
def postgres_session_factory(postgres_db):
    yield orm.sessionmaker(bind=postgres_db)


@pytest.fixture
def postgres_session(postgres_session_factory):
    return postgres_session_factory()


@pytest.fixture
def mappers():
    orm.start_mappers()
    yield
    orm.clear_mappers()


@retry(stop=stop_after_delay(5))
def wait_for_postgres_to_come_up(engine):
    return engine.connect()


@retry(stop=stop_after_delay(5))
def wait_for_webapp_to_come_up():
    url = config.get_api_url()
    return requests.get(url)


@retry(stop=stop_after_delay(10))
def wait_for_redis_to_come_up():
    r = redis.Redis(**config.get_redis_host_and_port())
    return r.ping()


def wait_for_redis_pubsub_to_come_up():
    stop_after_attempt = 10
    r = redis.Redis(**config.get_redis_host_and_port())
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe(ChannelEventConsumerOnline.channel_name)
    for _ in range(stop_after_attempt):
        r.publish(ChannelEventConsumerPing.channel_name, 'ping')
        m = pubsub.get_message(timeout=1.0)
        if m is not None:
            return True
    raise Exception


@pytest.fixture
def restart_api():
    # (Path(__file__).parent / "../src/allocation/entrypoints/flask_app.py").touch()
    # time.sleep(0.5)
    wait_for_webapp_to_come_up()


@pytest.fixture(scope="module")
def restart_redis_pubsub():
    wait_for_redis_to_come_up()
    if not shutil.which("docker-compose"):
        print("skipping restart, assumes running in container")
        return
    subprocess.run(
        ["docker-compose", "restart", "-t", "0", "redis_pubsub"],
        check=True,
    )
    wait_for_redis_pubsub_to_come_up()