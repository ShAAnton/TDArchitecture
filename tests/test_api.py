import pytest
import config
import requests
import uuid


def random_suffix():
    return uuid.uuid4().hex[:6]

def random_sku(name=""):
    return f"sku-{name}-{random_suffix()}"

def random_batch_ref(name=""):
    return f"batch-{name}-{random_suffix()}"

def random_order_id(name=""):
    return f"order-{name}-{random_suffix()}"


@pytest.mark.usefixtures('restart_api')
def test_happy_path_returns_201_and_allocated_batch(add_stock):
    sku, other_sku = random_sku(), random_sku('other')
    early_batch = random_batch_ref(1)
    later_batch = random_batch_ref(2)
    other_batch = random_batch_ref(3)
    add_stock([
        (later_batch, sku, 100, '2026-03-17'),
        (early_batch, sku, 100, '2026-03-16'),
        (other_batch, other_sku, 100, None)
    ])
    data = {'order_id': random_order_id(), 'sku': sku, 'quantity': 3}
    url = config.get_api_url()
    r = requests.post(f'{url}/allocate', json=data)
    assert r.status_code == 201
    assert r.json()['batch_ref'] == early_batch

@pytest.mark.usefixtures('restart_api')
def test_unhappy_path_returns_400_and_error_message():
    unknown_sku, order_id = random_sku(), random_order_id()
    data = {'order_id': order_id, 'sku': unknown_sku, 'quantity': 20}
    url = config.get_api_url()
    r = requests.post(f'{url}/allocate', json=data)
    assert r.status_code == 400
    assert r.json()['message'] == f'Invalid sku {unknown_sku}'


def post_to_add_batch():
    pass

@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_deallocate(add_stock):
    sku, order1, order2 = random_sku(), random_order_id(), random_order_id()
    batch_ref = random_batch_ref()
    # post_to_add_batch(batch_ref, sku, 100, "2011-01-02")
    add_stock([
        (batch_ref, sku, 100, '2026-03-17'),
    ])
    url = config.get_api_url()
    # fully allocate
    r = requests.post(
        f"{url}/allocate",
        json={"order_id": order1,
              "sku": sku,
              "quantity": 100}
    )
    assert r.json()["batch_ref"] == batch_ref

    # cannot allocate second order
    r = requests.post(
        f"{url}/allocate",
        json={"order_id": order2,
              "sku": sku,
              "quantity": 100}
    )
    assert r.status_code == 400

    # deallocate
    r = requests.post(
        f"{url}/deallocate",
        json={"order_id": order1,
              "sku": sku,
              "quantity": 100}
    )
    assert r.status_code == 201

    # now we can allocate second order
    r = requests.post(
        f"{url}/allocate",
        json={"order_id": order2,
              "sku": sku,
              "quantity": 100}
    )
    assert r.status_code == 201
    assert r.json()["batch_ref"] == batch_ref