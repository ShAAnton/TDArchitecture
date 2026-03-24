import repository
import model
import services
import pytest
# from datetime import date, timedelta
from typing import Iterable


class FakeRepository(repository.AbstractRepository):
    def __init__(self, batches: Iterable[model.Batch] | None = None):
        self._batches = set(batches) if batches else set()

    def add(self, batch):
        self._batches.add(batch)

    def get(self, reference):
        return next(b for b in self._batches if b.reference == reference)

    def list(self):
        return list(self._batches)

    @staticmethod
    def for_batch(ref, sku, qty, eta=None):
        batch = model.Batch(ref, sku, qty, eta)
        return FakeRepository([batch])


class FakeSession:
    commited = False

    def commit(self):
        self.commited = True


# today = date.today()
# tomorrow = today + timedelta(days=1)
# later = tomorrow + timedelta(days=10)


def test_add_batch():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "CRUNCHY-ARMCHAIRT", 100, None, repo, session)
    assert repo.get("b1") is not None
    assert session.commited is True


def test_allocate_returns_allocation():
    sku = "COMPLICATED-LAMP"
    repo, session = FakeRepository.for_batch("b1", sku, 100, eta=None), FakeSession()
    result = services.allocate("o1", sku, 10, repo, session)
    assert result == "b1"


def test_error_for_invalid_sku():
    sku = "NONEXISTENTSKU"
    repo = FakeRepository.for_batch("b1", "AREALSKU", 100, eta=None)
    with pytest.raises(services.InvalidSku, match=f"Invalid sku {sku}"):
        services.allocate("o1", sku, 10, repo, FakeSession())


def test_commit():
    sku = "OMINOUS-MIRROR"
    repo = FakeRepository.for_batch("b1", sku, 100, eta=None)
    session = FakeSession()
    services.allocate("o1", sku, 10, repo, session)
    assert session.commited is True


def test_deallocate_decrements_available_quantity():
    sku = "BLUE-PLINTH"
    repo, session = FakeRepository.for_batch("b1", sku, 100), FakeSession()
    services.allocate("o1", sku, 10, repo, session)
    batch = repo.get(reference="b1")
    assert batch.available_quantity == 90
    services.deallocate("o1", "BLUE-PLINTH", 10, repo, session)
    assert batch.available_quantity == 100


def test_deallocate_decrements_correct_quantity():
    sku = "GOODBATCH"
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", sku, quantity=100, eta=None, repo=repo, session=session)
    batch = repo.get(reference="b1")
    wrong_quantity_line = ("o1", sku, 5)
    services.allocate("o1", sku, 10, repo, session)
    try:
        services.deallocate(*wrong_quantity_line, repo, session)
    except model.NotAllocatedLine:
        pass
    assert batch.available_quantity == 90


def test_trying_to_deallocate_unallocated_batch():
    sku = "SOLONG_BATCH"
    repo, session = FakeRepository.for_batch("b1", sku, 100, eta=None), FakeSession()
    not_allocated_line = ("o1", sku, 10)
    with pytest.raises(model.NotAllocatedLine, match=f"Can not deallocate not allocated line {sku}"):
        services.deallocate(*not_allocated_line, repo, session)


# def test_prefers_current_stock_batches_to_shipments():
#     sku = "RETRO-CLOCK"
#     in_stock_batch = model.Batch("in-stock-batch", sku, 100, eta=None)
#     shipment_batch = model.Batch("shipment-batch", sku, 100, eta=tomorrow)
#     line = model.OrderLine("oref", sku, 10)
#
#     services.allocate(line, [in_stock_batch, shipment_batch])