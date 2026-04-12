from allocation.adapters import repository
from allocation.service_layer import handlers
from allocation.service_layer import unit_of_work
from allocation.service_layer import message_bus
from allocation.domain import events
from allocation.domain import exceptions


import pytest
from typing import Iterable
from unittest import mock
from datetime import date


class FakeRepository(repository.AbstractRepository):
    def __init__(self, products: Iterable | None = None):
        self._product = set(products) if products else set()
        super().__init__()

    def _add(self, product):
        self._product.add(product)

    def _get(self, sku):
        return next((p for p in self._product if p.sku == sku), None)

    def list(self):
        return list(self._product)


class FakeUnitOfWork(unit_of_work.AbstractionUnitOfWork):
    def __init__(self):
        self.products = FakeRepository()
        self.commited = False

    def _commit(self):
        self.commited = True

    def rollback(self):
        pass


class TestAddBatch:
    @staticmethod
    def test_add_batch_for_new_product():
        uow = FakeUnitOfWork()
        sku = "CRUNCHY-ARMCHAIR"
        message_bus.handle(
            [
                events.BatchCreated("b1", sku, 100, None)
            ], uow)
        assert uow.products.get(sku) is not None
        assert uow.commited is True

    @staticmethod
    def test_add_batch_for_existing_product():
        uow = FakeUnitOfWork()
        sku = "GARISH-RUG"
        message_bus.handle([
            events.BatchCreated("b1", sku, 100, None),
            events.BatchCreated("b2", sku, 99, None)
        ], uow)
        assert "b2" in [b.reference for b in uow.products.get(sku).batches]


class TestAllocate:

    @staticmethod
    def test_allocate_returns_allocation():
        sku = "COMPLICATED-LAMP"
        uow = FakeUnitOfWork()
        result = message_bus.handle([
            events.BatchCreated("b1", sku, 100, None),
            events.AllocationRequired("o1", sku, 10)
        ], uow)
        assert result.pop() == "b1"

    @staticmethod
    def test_allocate_error_for_invalid_sku():
        sku, invalid_sku = "AREALSKU", "NONEXISTENTSKU"
        uow = FakeUnitOfWork()
        message_bus.handle([
            events.BatchCreated("b1", sku, 100, None)
        ], uow)
        with pytest.raises(exceptions.InvalidSku, match=f"Invalid sku {invalid_sku}"):
            message_bus.handle([
                events.AllocationRequired("o1", invalid_sku, 10)
            ], uow)

    @staticmethod
    def test_allocate_commits():
        sku = "OMINOUS-MIRROR"
        uow = FakeUnitOfWork()
        message_bus.handle([
            events.BatchCreated("b1", sku, 100, None),
            events.AllocationRequired("o1", sku, 10)
        ], uow)
        assert uow.commited is True

    @staticmethod
    def test_sends_email_on_out_of_stock_error():
        uow = FakeUnitOfWork()
        sku = "POPULAR-CURTAINS"
        message_bus.handle([
            events.BatchCreated("b1", sku, 9, None)
        ], uow)

        with mock.patch("allocation.adapters.email.send_email") as mock_send_email:
            message_bus.handle([
                events.AllocationRequired("o1", sku, 10)
            ], uow)
            assert mock_send_email.call_args == mock.call(
                "stock@made.com",
                f"Out of stock for {sku}"
            )

    @staticmethod
    def test_trying_to_deallocate_unallocated_batch():
        sku = "SOLONG_BATCH"
        uow = FakeUnitOfWork()
        message_bus.handle([
            events.BatchCreated("b1", sku, 100, eta=None)
        ], uow)
        not_allocated_line = ("o1", sku, 10)
        with pytest.raises(exceptions.NotAllocatedLine, match=f"Can not deallocate not allocated line {sku}"):
            message_bus.handle([
                events.DeallocationRequired(*not_allocated_line)
            ], uow)


class TestChangeBatchQuantity:

    @staticmethod
    def test_changes_available_quantity():
        sku = "ADORABLE-SETTEE"
        uow = FakeUnitOfWork()
        message_bus.handle([
            events.BatchCreated("batch1", sku, 100, None)
        ], uow)
        [batch] = uow.products.get(sku=sku).batches
        assert batch.available_quantity == 100

        message_bus.handle([
            events.BatchQuantityChanged("batch1", 50)
        ], uow)

        assert batch.available_quantity == 50

    @staticmethod
    def test_reallocate_if_necessary():
        uow = FakeUnitOfWork()
        sku = "INDIFFERENT-TABLE"
        message_bus.handle([
            events.BatchCreated("batch1", sku, 50, None),
            events.BatchCreated("batch2", sku, 50, date.today()),
            events.AllocationRequest("order1", sku, 20),
            events.AllocationRequest("order2", sku, 20),
        ], uow)
        [batch1, batch2] = uow.products.get(sku=sku).batches
        assert batch1.available_quantity == 10

        message_bus.handle([
            events.BatchQuantityChanged("batch1", 20)
        ], uow)

        # order1 or order2 will be deallocated, so we"ll have 25 - 20 * 1
        assert batch1.available_quantity == 5
        # and 20 will be reallocated to the next batch
        assert batch2.available_quantity == 30

    @staticmethod
    def test_deallocate_decrements_available_quantity():
        sku = "BLUE-PLINTH"
        uow = FakeUnitOfWork()
        message_bus.handle([
            events.BatchCreated("b1", sku, 100, None),
            events.AllocationRequired("o1", sku, 10),
            events.DeallocationRequired("o1", sku, 10)
        ], uow)
        [batch] = uow.products.get(sku).batches
        assert batch.available_quantity == 100

    @staticmethod
    def test_deallocate_decrements_correct_quantity():
        sku = "GOODBATCH"
        uow = FakeUnitOfWork()
        message_bus.handle([
            events.BatchCreated("b1", sku, quantity=100, eta=None),
            events.AllocationRequired("o1", sku, 10)
        ], uow)
        wrong_quantity_line = ("o1", sku, 5)
        try:
            message_bus.handle([
                events.DeallocationRequired(*wrong_quantity_line)
            ], uow)
        except exceptions.NotAllocatedLine:
            pass
        [batch] = uow.products.get(sku).batches
        assert batch.available_quantity == 90

