from allocation.adapters import repository
from allocation.service_layer import handlers
from allocation.service_layer import unit_of_work
from allocation.service_layer import message_bus
from allocation.domain import events, commands
from allocation.domain import exceptions
import allocation

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

    def _get_by_batch_ref(self, batch_ref: str):
        for product in self._product:
            for batch in product.batches:
                if batch.reference == batch_ref:
                    return product
        return None

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
        mb = message_bus.MessageBus(FakeUnitOfWork())
        sku = "CRUNCHY-ARMCHAIR"
        mb.handle(commands.CreateBatch("b1", sku, 100, None))
        assert mb.uow.products.get(sku) is not None
        assert mb.uow.commited is True

    @staticmethod
    def test_add_batch_for_existing_product():
        mb = message_bus.MessageBus(FakeUnitOfWork())
        sku = "GARISH-RUG"
        messages_history = [
            commands.CreateBatch("b1", sku, 100, None),
            commands.CreateBatch("b2", sku, 99, None)
        ]
        for message in messages_history:
            mb.handle(message)
        assert "b2" in [b.reference for b in mb.uow.products.get(sku).batches]


class TestAllocate:

    @staticmethod
    def test_allocate_returns_allocation():
        sku = "COMPLICATED-LAMP"
        mb = message_bus.MessageBus(FakeUnitOfWork())
        mb.handle(commands.CreateBatch("b1", sku, 100, None))
        result = mb.handle(commands.Allocate("o1", sku, 10))
        assert result.pop() == "b1"

    @staticmethod
    def test_allocate_error_for_invalid_sku():
        sku, invalid_sku = "AREALSKU", "NONEXISTENTSKU"
        mb = message_bus.MessageBus(FakeUnitOfWork())
        mb.handle(commands.CreateBatch("b1", sku, 100, None))
        with pytest.raises(exceptions.InvalidSku, match=f"Invalid sku {invalid_sku}"):
            mb.handle(commands.Allocate("o1", invalid_sku, 10))

    @staticmethod
    def test_allocate_commits():
        sku = "OMINOUS-MIRROR"
        mb = message_bus.MessageBus(FakeUnitOfWork())
        mb.handle(commands.CreateBatch("b1", sku, 100, None))
        mb.handle(commands.Allocate("o1", sku, 10))
        assert mb.uow.commited is True

    @staticmethod
    def test_sends_email_on_out_of_stock_error():
        mb = message_bus.MessageBus(FakeUnitOfWork())
        sku = "POPULAR-CURTAINS"
        mb.handle(commands.CreateBatch("b1", sku, 9, None))

        with mock.patch("allocation.adapters.email.send_email") as mock_send_email:
            mb.handle(commands.Allocate("o1", sku, 10))
            assert mock_send_email.call_args == mock.call(
                "stock@made.com",
                f"Out of stock for {sku}"
            )

    @staticmethod
    def test_trying_to_deallocate_unallocated_batch():
        sku = "SOLONG_BATCH"
        mb = message_bus.MessageBus(FakeUnitOfWork())
        mb.handle(commands.CreateBatch("b1", sku, 100, eta=None))
        not_allocated_line = ("o1", sku, 10)
        with pytest.raises(exceptions.NotAllocatedLine, match=f"Can not deallocate not allocated line {sku}"):
            mb.handle(commands.Deallocate(*not_allocated_line))


class TestChangeBatchQuantity:

    @staticmethod
    def test_changes_available_quantity():
        sku = "ADORABLE-SETTEE"
        mb = message_bus.MessageBus(FakeUnitOfWork())
        mb.handle(commands.CreateBatch("batch1", sku, 100, None))
        [batch] = mb.uow.products.get(sku=sku).batches
        assert batch.available_quantity == 100

        mb.handle(commands.ChangeBatchQuantity("batch1", 50))

        assert batch.available_quantity == 50

    @staticmethod
    def test_reallocate_if_necessary():
        mb = message_bus.MessageBus(FakeUnitOfWork())
        sku = "INDIFFERENT-TABLE"
        event_history = [
            commands.CreateBatch("batch1", sku, 50, None),
            commands.CreateBatch("batch2", sku, 50, date.today()),
            commands.Allocate("order1", sku, 20),
            commands.Allocate("order2", sku, 20),
        ]
        for event in event_history:
            mb.handle(event)
        [batch1, batch2] = mb.uow.products.get(sku=sku).batches
        assert batch1.available_quantity == 10
        assert batch2.available_quantity == 50

        mb.handle(commands.ChangeBatchQuantity("batch1", 20))

        # order1 or order2 will be deallocated, so we"ll have 20 - 20 * 1
        assert batch1.available_quantity == 0
        # and 20 will be reallocated to the next batch
        assert batch2.available_quantity == 30

    @staticmethod
    def test_deallocate_decrements_available_quantity():
        sku = "BLUE-PLINTH"
        mb = message_bus.MessageBus(FakeUnitOfWork())
        event_history = [
            commands.CreateBatch("b1", sku, 100, None),
            commands.Allocate("o1", sku, 10),
            commands.Deallocate("o1", sku, 10)
        ]
        for event in event_history:
            mb.handle(event)
        [batch] = mb.uow.products.get(sku).batches
        assert batch.available_quantity == 100

    @staticmethod
    def test_deallocate_decrements_correct_quantity():
        sku = "GOODBATCH"
        mb = message_bus.MessageBus(FakeUnitOfWork())
        mb.handle(commands.CreateBatch("b1", sku, quantity=100, eta=None))
        mb.handle(commands.Allocate("o1", sku, 10))
        wrong_quantity_line = ("o1", sku, 5)
        try:
            mb.handle(commands.Deallocate(*wrong_quantity_line))
        except exceptions.NotAllocatedLine:
            pass
        [batch] = mb.uow.products.get(sku).batches
        assert batch.available_quantity == 90

