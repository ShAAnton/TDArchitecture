from allocation.domain import model
from allocation.service_layer.unit_of_work import AbstractionUnitOfWork


class InvalidSku(Exception):
    pass

class NotAllocatedLine(Exception):
    pass

def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def add_batch(batch_ref, sku, quantity, eta, uow: AbstractionUnitOfWork):
    with uow:
        product = uow.products.get(sku)
        if product is None:
            product = model.Product(sku, [])
            uow.products.add(product)
        batch = model.Batch(batch_ref, sku, quantity, eta)
        product.batches.append(batch)
        uow.commit()


def allocate(order_id: str, sku: str, quantity: int, uow: AbstractionUnitOfWork) -> str:
    with uow:
        products = uow.products.get(sku)
        if products is None:
            raise InvalidSku(f'Invalid sku {sku}')
        order_line = model.OrderLine(order_id, sku, quantity)
        batch_ref = products.allocate(order_line)
        uow.commit()
        return batch_ref

def deallocate(order_id: str, sku: str, quantity: int, uow: AbstractionUnitOfWork):
    with uow:
        batches = uow.batches.list()
        if not is_valid_sku(sku, batches):
            raise InvalidSku(f'Invalid sku {sku}')
        order_line = model.OrderLine(order_id, sku, quantity)
        try:
            batch_ref = model.deallocate(order_line, batches)
        except model.NotAllocatedLine as e:
            raise NotAllocatedLine(e.args)
        uow.commit()
        return batch_ref
