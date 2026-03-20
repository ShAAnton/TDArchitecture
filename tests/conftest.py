import pytest
import time
import requests
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker, clear_mappers
import orm
import config


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    orm.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(in_memory_db):
    orm.start_mappers()
    yield sessionmaker(bind=in_memory_db)()
    clear_mappers()


def wait_for_postgres_to_come_up(engine):
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            return engine.connect()
        except OperationalError:
            time.sleep(0.5)
    pytest.fail("Postgres never came up")


def wait_for_webapp_to_come_up():
    deadline = time.time() + 10
    url = config.get_api_url()
    while time.time() < deadline:
        try:
            return requests.get(url)
        except ConnectionError:
            time.sleep(0.5)
    pytest.fail("API never came up")

@pytest.fixture(scope="session")
def postgres_db():
    engine = create_engine(config.get_postgres_uri())
    wait_for_postgres_to_come_up(engine)
    orm.metadata.create_all(engine)
    return engine


@pytest.fixture
def postgres_session(postgres_db):
    orm.start_mappers()
    yield sessionmaker(bind=postgres_db)()
    clear_mappers()


@pytest.fixture
def add_stock(postgres_session):
    batches_added =set()
    skus_added = set()

    # Some lost function
    def _add_stock(lines):
        for ref, sku, qty, eta in lines:
            sql_insert = orm.text(
                'INSERT INTO batches (reference, sku, _purchased_quantity, eta) '
                'VALUES (:ref, :sku, :qty, :eta)'
            )
            postgres_session.execute(sql_insert,
                                     dict(ref=ref, sku=sku, qty=qty, eta=eta)
                                     )
            sql_select = orm.text(
                'SELECT batch_id FROM batches '
                'WHERE reference = :ref '
                'AND sku = :sku'
            )
            [[batch_id]] = postgres_session.execute(sql_select,
                                                    dict(ref=ref, sku=sku)
                                                    )
            batches_added.add(batch_id)
            skus_added.add(sku)
        postgres_session.commit()

    yield _add_stock

    for batch_id in batches_added:
        sql_delete = orm.text(
            'DELETE FROM allocations '
            'WHERE batch_id = :batch_id '
        )
        postgres_session.execute(sql_delete,
                                 dict(batch_id=batch_id))
        sql_delete = orm.text(
            'DELETE FROM batches '
            'WHERE batch_id = :batch_id '
        )
        postgres_session.execute(sql_delete,
                                 dict(batch_id=batch_id))
    for sku in skus_added:
        sql_delete = orm.text(
                'DELETE FROM order_lines '
                'WHERE sku = :sku '
            )
        postgres_session.execute(sql_delete,
                                     dict(sku=sku))
        postgres_session.commit()

@pytest.fixture
def restart_api():
    (Path(__file__).parent / "flask_app.py").touch()
    time.sleep(0.5)
    wait_for_webapp_to_come_up()