import requests
from allocation import config


def post_to_add_batch(batch_ref, sku, quantity, eta=None):
    url = config.get_api_url()
    post_allocate_param = {
        "batch_ref": batch_ref,
        "sku": sku,
        "quantity": quantity,
        "eta": eta
    }
    r = requests.post(
        f"{url}/add_batch",
        json=post_allocate_param
    )
    assert r.status_code == 201

def post_to_allocate(order_id, sku, quantity, expect_success=True):
    url = config.get_api_url()
    post_allocate_param = {
        'order_id': order_id,
        'sku': sku,
        'quantity': quantity
    }
    r = requests.post(
        f'{url}/allocate',
        json=post_allocate_param
    )
    if expect_success:
        assert r.status_code == 201
    return r

def post_to_deallocate(order_id, sku, quantity, expect_success=True):
    url = config.get_api_url()
    post_allocate_param = {
        'order_id': order_id,
        'sku': sku,
        'quantity': quantity
    }
    r = requests.post(
        f'{url}/deallocate',
        json=post_allocate_param
    )
    if expect_success:
        assert r.status_code == 201
    return r