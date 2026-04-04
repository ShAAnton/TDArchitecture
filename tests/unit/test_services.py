from allocation.adapters import repository
from allocation.service_layer import services
import allocation.service_layer.unit_of_work as unit_of_work
import pytest
from typing import Iterable


class FakeRepository(repository.AbstractRepository):
    def __init__(self, products: Iterable | None = None):
        self._product = set(products) if products else set()

    def add(self, product):
        self._product.add(product)

    def get(self, sku):
        return next((p for p in self._product if p.sku == sku), None)

    def list(self):
        return list(self._product)


class FakeUnitOfWork(unit_of_work.AbstractionUnitOfWork):
    def __init__(self):
        self.products = FakeRepository()
        self.commited = False

    def commit(self):
        self.commited = True

    def rollback(self):
        pass


def test_add_batch_for_new_product():
    uow = FakeUnitOfWork()
    sku = "CRUNCHY-ARMCHAIRT"
    services.add_batch("b1", sku, 100, None, uow)
    assert uow.products.get(sku) is not None
    assert uow.commited is True


def test_add_batch_for_existing_product():
    uow = FakeUnitOfWork()
    sku = "GARISH-RUG"
    services.add_batch("b1", sku, 100, None, uow)
    services.add_batch("b2", sku, 99, None, uow)
    assert "b2" in [b.reference for b in uow.products.get(sku).batches]

def test_allocate_returns_allocation():
    sku = "COMPLICATED-LAMP"
    uow = FakeUnitOfWork()
    services.add_batch("b1", sku, 100, None, uow)
    result = services.allocate("o1", sku, 10, uow)
    assert result == "b1"


def test_error_for_invalid_sku():
    sku, invalid_sku = "AREALSKU", "NONEXISTENTSKU"
    uow = FakeUnitOfWork()
    services.add_batch("b1", sku, 100, None, uow)
    with pytest.raises(services.InvalidSku, match=f"Invalid sku {invalid_sku}"):
        services.allocate("o1", invalid_sku, 10, uow)


def test_allocate_commits():
    sku = "OMINOUS-MIRROR"
    uow = FakeUnitOfWork()
    services.add_batch("b1", sku, 100, None, uow)
    services.allocate("o1", sku, 10, uow)
    assert uow.commited is True


def test_deallocate_decrements_available_quantity():
    sku = "BLUE-PLINTH"
    uow = FakeUnitOfWork()
    services.add_batch("b1", sku, 100, None, uow)
    services.allocate("o1", sku, 10, uow)
    batch = uow.products.get(sku).batches[0]
    assert batch.available_quantity == 90
    services.deallocate("o1", sku, 10, uow)
    assert batch.available_quantity == 100


def test_deallocate_decrements_correct_quantity():
    sku = "GOODBATCH"
    uow = FakeUnitOfWork()
    services.add_batch("b1", sku, quantity=100, eta=None, uow=uow)
    batch = uow.products.get(sku).batches[0]
    wrong_quantity_line = ("o1", sku, 5)
    services.allocate("o1", sku, 10, uow)
    try:
        services.deallocate(*wrong_quantity_line, uow)
    except services.NotAllocatedLine:
        pass
    assert batch.available_quantity == 90


def test_trying_to_deallocate_unallocated_batch():
    sku = "SOLONG_BATCH"
    uow = FakeUnitOfWork()
    services.add_batch("b1", sku, 100, eta=None, uow=uow)
    not_allocated_line = ("o1", sku, 10)
    with pytest.raises(services.NotAllocatedLine, match=f"Can not deallocate not allocated line {sku}"):
        services.deallocate(*not_allocated_line, uow)


# def test_prefers_current_stock_batches_to_shipments():
#     sku = "RETRO-CLOCK"
#     in_stock_batch = model.Batch("in-stock-batch", sku, 100, eta=None)
#     shipment_batch = model.Batch("shipment-batch", sku, 100, eta=tomorrow)
#     line = model.OrderLine("oref", sku, 10)
#
#     services.allocate(line, [in_stock_batch, shipment_batch])