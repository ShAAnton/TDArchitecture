import model
import repository
from repository import AbstractRepository


class InvalidSku(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}

def allocate(line: model.OrderLine, repo: AbstractRepository, session: repository.Session) -> str:
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f'Invalid sku {line.sku}')
    batch_ref = model.allocate(line, batches)
    session.commit()
    return batch_ref