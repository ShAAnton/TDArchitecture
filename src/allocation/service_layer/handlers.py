from allocation.domain import model, events
from allocation.adapters import email
from allocation.service_layer.unit_of_work import AbstractionUnitOfWork

class InvalidSku(Exception):
    pass


class NotAllocatedLine(Exception):
    pass


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
        product = uow.products.get(sku)
        if product is None:
            raise InvalidSku(f'Invalid sku {sku}')
        order_line = model.OrderLine(order_id, sku, quantity)
        batch_ref = product.deallocate(order_line)
        if batch_ref is None:
            raise NotAllocatedLine(f"Can not deallocate not allocated line {sku}")
        uow.commit()
        return batch_ref

def send_out_of_stock_notification(event: events.OutOfStock, uow: AbstractionUnitOfWork):
    email.send_mail(
        'stock@made.com',
        f'Out of stock for {event.sku}'
    )