from allocation.domain import model, events, exceptions, commands
from allocation.service_layer.unit_of_work import AbstractionUnitOfWork, SqlAlchemyUnitOfWork
from allocation.adapters import notifications, eventpublisher
from dataclasses import asdict
import abc


class Handler(abc.ABC):

    @abc.abstractmethod
    def __call__(self, *args, **kwargs):
        raise NotImplementedError


class AddBatchHandler(Handler):

    def __init__(self, uow: AbstractionUnitOfWork):
        self.uow = uow

    def __call__(self, command: commands.CreateBatch):
        with self.uow:
            product = self.uow.products.get(command.sku)
            if product is None:
                product = model.Product(command.sku, [])
                self.uow.products.add(product)
            batch = model.Batch(command.reference, command.sku, command.quantity, command.eta)
            product.batches.append(batch)
            self.uow.commit()


class AllocateHandler(Handler):

    def __init__(self, uow: AbstractionUnitOfWork):
        self.uow = uow

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


class DeallocateHandler(Handler):

    def __init__(self, uow: AbstractionUnitOfWork):
        self.uow = uow

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

class ChangeBatchQuantityHandler(Handler):

    def __init__(self, uow: AbstractionUnitOfWork):
        self.uow = uow

    def __call__(self, command: commands.ChangeBatchQuantity):
        with self.uow:
            product = self.uow.products.get_by_batch_ref(command.reference)
            product.change_batch_quantity(batch_ref=command.reference, quantity=command.quantity)
            self.uow.commit()


class SendOutOfStockNotificationHandler(Handler):

    def __init__(self, notifications: notifications.Notification):
        self.notifications_ = notifications

    def __call__(self, event: events.OutOfStock):
        self.notifications_.send(
            'stock@made.com',
            f'Out of stock for {event.sku}'
        )


class PublishAllocatedEventHandler(Handler):

    def __init__(self, publish: eventpublisher.Publisher):
        self.publish = publish

    def __call__(self, event: events.Allocated):
        self.publish.publish("line_allocated", event)


class AddAllocationToReadModelHandler(Handler):

    def __init__(self, uow: AbstractionUnitOfWork):
        self.uow = uow

    def __call__(self, event: events.Allocated):
        with self.uow:
            self.uow.session.execute(
                'INSERT INTO allocations_view (order_id, sku, batch_ref)'
                ' VALUES (:order_id, :sku, :batch_ref)',
                dict(order_id=event.order_id, sku=event.sku, batch_ref=event.batch_ref)
            )
            self.uow.commit()


class ReallocateHandler(Handler):

    def __init__(self, uow: AbstractionUnitOfWork):
        self.uow = uow

    def __call__(self, event: events.Deallocated):
        with self.uow:
            product = self.uow.products.get(event.sku)
            product.events.append(commands.Allocate(**asdict(event)))
            self.uow.commit()


class RemoveAllocationFromReadModel(Handler):

    def __init__(self, uow: AbstractionUnitOfWork):
        self.uow = uow

    def __call__(self, event: events.Deallocated):
        with self.uow:
            self.uow.session.execute(
                'DELETE FROM allocations_view '
                ' WHERE order_id = :order_id AND sku = :sku',
                dict(order_id=event.order_id, sku=event.sku),
            )
            self.uow.commit()


EVENT_HANDLERS = {
    events.Allocated: [
        PublishAllocatedEventHandler,
        AddAllocationToReadModelHandler,
    ],
    events.Deallocated: [
        RemoveAllocationFromReadModel
    ],
    events.OutOfStock: [
        SendOutOfStockNotificationHandler
    ],
}
COMMAND_HANDLERS = {
    commands.CreateBatch: AddBatchHandler,
    commands.Allocate: AllocateHandler,
    commands.Deallocate: DeallocateHandler,
    commands.Reallocate: ReallocateHandler,
    commands.ChangeBatchQuantity: ChangeBatchQuantityHandler
}
