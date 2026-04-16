from allocation.domain import model, events, exceptions, commands
from allocation.adapters import email
from allocation.service_layer.unit_of_work import AbstractionUnitOfWork


def add_batch(command: commands.CreateBatch, uow: AbstractionUnitOfWork):
    with uow:
        product = uow.products.get(command.sku)
        if product is None:
            product = model.Product(command.sku, [])
            uow.products.add(product)
        batch = model.Batch(command.reference, command.sku, command.quantity, command.eta)
        product.batches.append(batch)
        uow.commit()


def allocate(command: commands.Allocate, uow: AbstractionUnitOfWork) -> str:
    with uow:
        products = uow.products.get(command.sku)
        if products is None:
            raise exceptions.InvalidSku(f'Invalid sku {command.sku}')
        order_line = model.OrderLine(command.order_id, command.sku, command.quantity)
        batch_ref = products.allocate(order_line)
        uow.commit()
        return batch_ref

def deallocate(command: commands.Deallocate, uow: AbstractionUnitOfWork):
    with uow:
        product = uow.products.get(command.sku)
        if product is None:
            raise exceptions.InvalidSku(f'Invalid sku {command.sku}')
        order_line = model.OrderLine(command.order_id, command.sku, command.quantity)
        batch_ref = product.deallocate(order_line)
        if batch_ref is None:
            raise exceptions.NotAllocatedLine(f"Can not deallocate not allocated line {command.sku}")
        uow.commit()
        return batch_ref


def change_batch_quantity(command: commands.ChangeBatchQuantity, uow: AbstractionUnitOfWork):
    # looks like bag no with uow
    product = uow.products.get_by_batch_ref(command.reference)
    product.change_batch_quantity(batch_ref=command.reference, quantity=command.quantity)
    uow.commit()


def send_out_of_stock_notification(event: events.OutOfStock, uow: AbstractionUnitOfWork):
    email.send_email(
        'stock@made.com',
        f'Out of stock for {event.sku}'
    )