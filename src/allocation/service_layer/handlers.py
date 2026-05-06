from allocation.domain import model, events, exceptions, commands
from allocation.adapters import notifications, redis_eventpublisher
from allocation.service_layer.unit_of_work import AbstractionUnitOfWork, SqlAlchemyUnitOfWork
from dataclasses import asdict
import abc


class CommandHandler(abc.ABC):

    def __init__(self, uow: AbstractionUnitOfWork):
        self.uow = uow

    @abc.abstractmethod
    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class AddBatchHandler(CommandHandler):

    def __call__(self, command: commands.CreateBatch):
        with self.uow:
            product = self.uow.products.get(command.sku)
            if product is None:
                product = model.Product(command.sku, [])
                self.uow.products.add(product)
            batch = model.Batch(command.reference, command.sku, command.quantity, command.eta)
            product.batches.append(batch)
            self.uow.commit()


class AllocateHandler(CommandHandler):

    def __call__(self, command: commands.Allocate):
        with self.uow:
            products = self.uow.products.get(command.sku)
            if products is None:
                raise exceptions.InvalidSku(f'Invalid sku {command.sku}')
            order_line = model.OrderLine(command.order_id, command.sku,
                                         command.quantity)
            batch_ref = products.allocate(order_line)
            self.uow.commit()
            return batch_ref


class DeallocateHandler(CommandHandler):

    def __call__(self, command: commands.Deallocate):
        with self.uow:
            product = self.uow.products.get(command.sku)
            if product is None:
                raise exceptions.InvalidSku(f'Invalid sku {command.sku}')
            order_line = model.OrderLine(command.order_id, command.sku, command.quantity)
            batch_ref = product.deallocate(order_line)
            if batch_ref is None:
                raise exceptions.NotAllocatedLine(f"Can not deallocate not allocated line {command.sku}")
            self.uow.commit()
            return batch_ref

class ChangeBatchQuantityHandler(CommandHandler):

    def __call__(self, command: commands.ChangeBatchQuantity):
        with self.uow:
            product = self.uow.products.get_by_batch_ref(command.reference)
            product.change_batch_quantity(batch_ref=command.reference, quantity=command.quantity)
            self.uow.commit()


def send_out_of_stock_notification(event: events.OutOfStock, notifications: notifications.Notification):
    notifications.send(
        'stock@made.com',
        f'Out of stock for {event.sku}'
    )


def publish_allocated_event(
    event: events.Allocated
):
    redis_eventpublisher.publish("line_allocated", event)

def add_allocation_to_read_model(
        event: events.Allocated,
        uow: SqlAlchemyUnitOfWork
):
    with uow:
        uow.session.execute(
            'INSERT INTO allocations_view (order_id, sku, batch_ref)'
            ' VALUES (:order_id, :sku, :batch_ref)',
            dict(order_id=event.order_id, sku=event.sku, batch_ref=event.batch_ref)
        )
        uow.commit()


class ReallocateHandler(CommandHandler):

    def __call__(self,
            event: events.Deallocated,
        ):
        with self.uow:
            product = self.uow.products.get(event.sku)
            product.events.append(commands.Allocate(**asdict(event)))
            self.uow.commit()

def remove_allocation_from_read_model(
        event: events.Deallocated,
        uow: SqlAlchemyUnitOfWork,
):
    with uow:
        uow.session.execute(
            'DELETE FROM allocations_view '
            ' WHERE order_id = :order_id AND sku = :sku',
            dict(order_id=event.order_id, sku=event.sku),
        )
        uow.commit()


EVENT_HANDLERS = {
    events.Allocated: [
        publish_allocated_event,
        add_allocation_to_read_model,
    ],
    events.Deallocated: [
        remove_allocation_from_read_model
    ],
    events.OutOfStock: [
        send_out_of_stock_notification
    ],
}
COMMAND_HANDLERS = {
    commands.CreateBatch: AddBatchHandler,
    commands.Allocate: AllocateHandler,
    commands.Deallocate: DeallocateHandler,
    commands.Reallocate: ReallocateHandler,
    commands.ChangeBatchQuantity: ChangeBatchQuantityHandler
}
