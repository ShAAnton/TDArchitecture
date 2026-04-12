from allocation.domain import model, events
from allocation.adapters import email
from allocation.service_layer.unit_of_work import AbstractionUnitOfWork


class InvalidSku(Exception):
    pass


class NotAllocatedLine(Exception):
    pass


def add_batch(event: events.BatchCreated, uow: AbstractionUnitOfWork):
    with uow:
        product = uow.products.get(event.sku)
        if product is None:
            product = model.Product(event.sku, [])
            uow.products.add(product)
        batch = model.Batch(event.batch_ref, event.sku, event.quantity, event.eta)
        product.batches.append(batch)
        uow.commit()


def allocate(event: events.AllocationRequired, uow: AbstractionUnitOfWork) -> str:
    with uow:
        products = uow.products.get(event.sku)
        if products is None:
            raise InvalidSku(f'Invalid sku {event.sku}')
        order_line = model.OrderLine(event.order_id, event.sku, event.quantity)
        batch_ref = products.allocate(order_line)
        uow.commit()
        return batch_ref

def deallocate(event: events.DeallocationRequired, uow: AbstractionUnitOfWork):
    with uow:
        product = uow.products.get(event.sku)
        if product is None:
            raise InvalidSku(f'Invalid sku {event.sku}')
        order_line = model.OrderLine(event.order_id, event.sku, event.quantity)
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