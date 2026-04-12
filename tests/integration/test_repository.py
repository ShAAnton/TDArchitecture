from allocation.domain import model
from allocation.adapters import repository

def test_get_by_batch_ref(session):
    repo = repository.SQLAlchemyRepository(session)
    b1 = model.Batch(ref='b1', sku='sku1', quantity=100, eta=None)
    b2 = model.Batch(ref='b2', sku='sku1', quantity=100, eta=None)
    b3 = model.Batch(ref='b3', sku='sku2', quantity=100, eta=None)
    p1 = model.Product(sku='sku1', batches=[b1, b2])
    p2 = model.Product(sku='sku2', batches=[b3])
    repo.add(p1)
    repo.add(p2)
    assert repo.get_by_batch_ref('b2') == p1
    assert repo.get_by_batch_ref('b3') == p2