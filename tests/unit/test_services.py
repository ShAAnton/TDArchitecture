import repository
import model
import services
import pytest
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


class FakeSession:
    commited = False

    def commit(self):
        self.commited = True


def test_returns_allocation():
    sku = "COMPLICATED-LAMP"
    line = model.OrderLine("o1", sku, 10)
    batch = model.Batch("b1", sku, 100, eta=None)
    repo = FakeRepository([batch])

    result = services.allocate(line, repo, FakeSession())
    assert result == "b1"


def test_error_for_invalid_sku():
    sku = "NONEXISTENTSKU"
    line = model.OrderLine("o1", sku, 10)
    batch = model.Batch("b1", "AREALSKU", 100, eta=None)
    repo = FakeRepository([batch])

    with pytest.raises(services.InvalidSku, match=f"Invalid sku {sku}"):
        services.allocate(line, repo, FakeSession())


def test_commit():
    sku = "OMINOUS-MIRROR"
    line = model.OrderLine("o1", sku, 10)
    batch = model.Batch("b1", sku, 100, eta=None)
    repo = FakeRepository([batch])
    session = FakeSession()
    services.allocate(line, repo, session)
    assert session.commited is True


def test_deallocate_decrements_available_quantity():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "BLUE-PLINTH", 100, None, repo, session)
    line = model.OrderLine("o1", "BLUE-PLINTH", 10)
    services.allocate(line, repo, session)
    batch = repo.get(reference="b1")
    assert batch.available_quantity == 90
    services.deallocate(line, repo, session)
    assert batch.available_quantity == 100


def test_deallocate_decrements_correct_quantity():
    sku = "GOODBATCH"
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", sku, quantity=100, eta=None, repo=repo, session=session)
    batch = repo.get(reference="b1")
    line = model.OrderLine("o1", sku, 10)
    wrong_quantity_line = model.OrderLine("o1", sku, 5)
    services.allocate(line, repo, session)
    try:
        services.deallocate(wrong_quantity_line, repo, session)
    except model.NotAllocatedLine:
        pass
    assert batch.available_quantity == 90


def test_trying_to_deallocate_unallocated_batch():
    sku = "SOLONG_BATCH"
    repo, session = FakeRepository(), FakeSession()
    services.add_batch("b1", sku, quantity=100, eta=None, repo=repo, session=session)
    not_allocated_line = model.OrderLine("o1", sku, 10)
    with pytest.raises(model.NotAllocatedLine, match=f"Can not deallocate not allocated line {not_allocated_line.sku}"):
        services.deallocate(not_allocated_line, repo, session)
