import model
import repository
from repository import AbstractRepository, Session


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def allocate(line: model.OrderLine, repo: AbstractRepository, session: Session) -> str:
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f'Invalid sku {line.sku}')
    batch_ref = model.allocate(line, batches)
    session.commit()
    return batch_ref


def add_batch(batch_ref, sku, quantity, eta, repo: AbstractRepository, session: Session):
    batch = model.Batch(batch_ref, sku, quantity, eta)
    repo.add(batch)
    session.commit()
    return batch.reference

def deallocate(line, repo: AbstractRepository, session):
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f'Invalid sku {line.sku}')
    batch_ref = model.deallocate(line, batches)
    session.commit()
    return batch_ref
