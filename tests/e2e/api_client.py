import requests
from allocation import config


def post_to_add_batch(batch_ref, sku, quantity, eta=None):
    url = config.get_api_url()
    r = requests.post(
        f"{url}/add_batch",
        json={"batch_ref": batch_ref,
              "sku": sku,
              "quantity": quantity,
              "eta": eta}
    )
    assert r.status_code == 201

def post_to_allocate(order_id, sku, quantity, expect_success=True):
    url = config.get_api_url()
    r = requests.post(f'{url}/allocate',
                      json={
                          "order_id": order_id,
                          "sku": sku,
                          "quantity": quantity
                      })
    if expect_success:
        assert r.status_code == 201
    return r