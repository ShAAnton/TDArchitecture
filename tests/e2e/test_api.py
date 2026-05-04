import pytest
from ..random_refs import random_sku, random_batch_ref, random_order_id
from . import api_client

@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures('restart_api')
def test_happy_path_returns_201_and_allocated_batch():
    sku, other_sku = random_sku(), random_sku('other')
    batch_1 = random_batch_ref(1)
    batch_2 = random_batch_ref(2)
    batch_3 = random_batch_ref(3)
    api_client.post_to_add_batch(batch_1, sku, 100, '2026-03-17')
    api_client.post_to_add_batch(batch_2, sku, 100, '2026-03-16')
    api_client.post_to_add_batch(batch_3, other_sku, 100, None)
    order_id = random_order_id()
    api_client.post_to_allocate(order_id, sku, 3)

    response = api_client.get_allocation(order_id)
    assert response.ok
    assert response.json() == [
        {"sku": sku, "batch_ref": batch_2}
    ]

@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures('restart_api')
def test_unhappy_path_returns_400_and_error_message():
    unknown_sku, order_id = random_sku(), random_order_id()
    response = api_client.post_to_allocate(order_id, unknown_sku, 20, expect_success=False)

    assert response.status_code == 400
    assert response.json()['message'] == f'Invalid sku {unknown_sku}'

    response = api_client.get_allocation(order_id)
    assert response.status_code == 404


@pytest.mark.usefixtures("postgres_db")
@pytest.mark.usefixtures("restart_api")
def test_deallocate():
    sku, order1, order2 = random_sku(), random_order_id(), random_order_id()
    batch_ref = random_batch_ref()
    api_client.post_to_add_batch(batch_ref, sku, 100, "2026-05-04")

    # fully allocate
    api_client.post_to_allocate(order1, sku, 100)
    # deallocate
    api_client.post_to_deallocate(order1, sku, 100)

    response = api_client.get_allocation(order1)
    assert response.status_code == 404

    # now we can allocate second order
    response = api_client.post_to_allocate(order2, sku, 100)
    assert response.status_code == 201


    response = api_client.get_allocation(order2)
    assert response.json() == [
        {"sku": sku, "batch_ref": batch_ref}
    ]