from datetime import date, timedelta
import pytest

from model import *

today = date.today()
tomorrow = today + timedelta(days=1)
later = tomorrow + timedelta(days=10)


def make_batch_and_line(sku, batch_qty, line_qty):
    return (
        Batch("batch-001", sku, batch_qty, eta=date.today()),
        OrderLine("order-123", sku, line_qty)
    )


def test_allocating_to_a_batch_reduces_the_available_quantity():
    batch, line = make_batch_and_line(sku="SMALL-TABLE", batch_qty=20, line_qty=2)
    batch.allocate(line)
    assert batch.available_quantity == 18


def test_can_allocate_if_available_greater_than_required():
    batch, line = make_batch_and_line("ELEGANT-LAMP", batch_qty=20, line_qty=2)
    assert batch.can_allocate(line)


def test_cannot_allocate_if_available_smaller_than_required():
    batch, line = make_batch_and_line("ELEGANT-LAMP", batch_qty=10, line_qty=20)
    assert batch.can_allocate(line) is False


def test_can_allocate_if_available_equal_to_required():
    batch, line = make_batch_and_line("ELEGANT-LAMP", batch_qty=10, line_qty=10)
    assert batch.can_allocate(line)


def test_cannot_allocate_if_skus_do_not_mathc():
    batch, line = make_batch_and_line("batch-001", "UNCOMFORTABLE-CHAIR", 100)
    different_sku_line = OrderLine("order-123", "EXPENSIVE-TOASTER", 10)
    assert batch.can_allocate(different_sku_line) is False


def test_can_only_deallocate_allocated_lines():
    batch, line = make_batch_and_line("DECORATIVE-TRINKET", 20, 2)
    batch.deallocate(line)
    assert batch.available_quantity == 20


def test_allocation_is_idempotent():
    batch, line = make_batch_and_line("ANGULAR-DESK", 20, 2)
    batch.allocate(line)
    batch.allocate(line)
    assert batch.available_quantity == 18


def test_prefers_current_stock_batches_to_shipment():
    sku = "RETRO-CLOCK"
    in_stock_batch = Batch("in-stock-batch", sku, 100, eta=None)
    shipment_batch = Batch("shipment-batch", sku, 100, eta=tomorrow)
    line = OrderLine("ored", sku, 10)

    allocate(line, [shipment_batch, in_stock_batch])

    assert in_stock_batch.available_quantity == 90
    assert shipment_batch.available_quantity == 100


def test_prefers_earlier_batches():
    sku = "MINIMALIST-SPOON"
    earliest = Batch("speedy-batch", sku, 100, eta=today)
    medium = Batch("normal-batch", sku, 100, eta=tomorrow)
    latest = Batch("slow-batch", sku, 100, eta=later)
    line = OrderLine("order1", sku, 10)

    allocate(line, [medium, earliest, latest])

    assert earliest.available_quantity == 90
    assert medium.available_quantity == 100
    assert latest.available_quantity == 100


def test_returns_allocated_batch_ref():
    sku = "HIGHBROW-POSTER"
    in_stock_batch = Batch("in-stock-batch-ref", sku, 100, eta=None)
    shipment_batch = Batch("shipment-batch-ref", sku, 100, eta=tomorrow)
    line = OrderLine("oref", sku, 10)
    allocation = allocate(line, [in_stock_batch, shipment_batch])
    assert allocation == in_stock_batch.reference


def test_raises_out_of_stock_exception_if_cannot_allocate():
    sku = "SMALL-FORK"
    batch = Batch("batch1", sku, 10, eta=today)
    allocate(OrderLine("order1", sku, 10), [batch])

    with pytest.raises(OutOfStock, match=sku):
        allocate(OrderLine("order2", sku, 1), [batch])


# def test_prefers_warehouse_batches_to_shipments():
#     pytest.fail("todo")
#
#
# def test_prefers_earlier_batches():
#     pytest.fail("todo")
