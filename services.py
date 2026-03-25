import model
import repository
from repository import AbstractRepository, Session
from model import NotAllocatedLine

class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def allocate(order_id: str, sku: str, quantity: int, repo: AbstractRepository, session: Session) -> str:
    batches = repo.list()
    if not is_valid_sku(sku, batches):
        raise InvalidSku(f'Invalid sku {sku}')
    order_line = model.OrderLine(order_id, sku, quantity)
    batch_ref = model.allocate(order_line, batches)
    session.commit()
    return batch_ref


def add_batch(batch_ref, sku, quantity, eta, repo: AbstractRepository, session: Session):
    batch = model.Batch(batch_ref, sku, quantity, eta)
    repo.add(batch)
    session.commit()
    return batch.reference

def deallocate(order_id: str, sku: str, quantity: int, repo: AbstractRepository, session):
    batches = repo.list()
    if not is_valid_sku(sku, batches):
        raise InvalidSku(f'Invalid sku {sku}')
    order_line = model.OrderLine(order_id, sku, quantity)
    batch_ref = model.deallocate(order_line, batches)
    session.commit()
    return batch_ref
