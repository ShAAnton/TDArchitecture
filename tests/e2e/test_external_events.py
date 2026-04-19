import json
import pytest
from tenacity import Retrying, RetryError, stop_after_delay
from . import api_client, redis_client
from ..random_refs import *



@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
@pytest.mark.usefixtures("restart_redis_pubsub")
def test_change_batch_quantity_leading_to_reallocation():
    # start with two batches and an order allocated to one of them
    order_id, sku = random_order_id(), random_sku()
    earlier_batch, later_batch = random_batch_ref("old"), random_batch_ref("newer")
    api_client.post_to_add_batch(earlier_batch, sku, quantity=10, eta="2026-04-18")
    api_client.post_to_add_batch(later_batch, sku, quantity=10, eta="2026-04-19")
    response = api_client.post_to_allocate(order_id, sku, 10)
    assert response.json()["batch_ref"] == earlier_batch

    subscription = redis_client.subscribe_to("line_allocated")

    # change quantity on allocated batch so it's less than our order
    redis_client.publish_message(
        "change_batch_quantity",
        {"batch_ref": earlier_batch, "quantity": 5}
    )

    # wait until we see a message saying the order has bee reallocated
    messages = []
    for attempt in Retrying(stop=stop_after_delay(3), reraise=True):
        with attempt:
            message = subscription.get_message(timeout=1)
            if message:
                messages.append(message)
                print(messages)
            data = json.loads(messages[-1]["data"])
            assert data["order_id"] == order_id
            assert data["batch_ref"] == later_batch
