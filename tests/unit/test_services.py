from allocation.adapters import repository
from allocation.service_layer import services
import allocation.service_layer.unit_of_work as unit_of_work
import pytest
from typing import Iterable


class FakeRepository(repository.AbstractRepository):
    def __init__(self, batches: Iterable | None = None):
        self._batches = set(batches) if batches else set()

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)


class FakeUnitOfWork(unit_of_work.AbstractionUnitOfWork):
    def __init__(self):
        self.batches = FakeRepository()
        self.commited = False

    def commit(self):
        self.commited = True

    def rollback(self):
        pass


def test_add_batch():
    uow = FakeUnitOfWork()
    services.add_batch("b1", "CRUNCHY-ARMCHAIRT", 100, None, uow)
    assert uow.batches.get("b1") is not None
    assert uow.commited is True


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


def test_allocate_commit():
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
    batch = uow.batches.get(reference="b1")
    assert batch.available_quantity == 90
    services.deallocate("o1", "BLUE-PLINTH", 10, uow)
    assert batch.available_quantity == 100


def test_deallocate_decrements_correct_quantity():
    sku = "GOODBATCH"
    uow = FakeUnitOfWork()
    services.add_batch("b1", sku, quantity=100, eta=None, uow=uow)
    batch = uow.batches.get(reference="b1")
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