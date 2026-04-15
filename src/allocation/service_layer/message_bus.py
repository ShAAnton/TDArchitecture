from typing import Dict, Type, List, Callable
import allocation.domain.events as events
import allocation.service_layer.handlers
from allocation.service_layer.unit_of_work import AbstractionUnitOfWork


class AbstractionMessageBus:
    HANDLERS: Dict[Type[events.Event], List[Callable]]

    def __init__(self, uow: AbstractionUnitOfWork):
        self.uow = uow

    def handle(self, event: events.Event):
        results, queue = list(), list()
        queue = [event]
        while queue:
            event = queue.pop(0)
            for handler in self.HANDLERS[type(event)]:
                results.append(handler(event, self.uow))
                queue.extend(self.uow.collect_new_events())
        return results


class MessageBus(AbstractionMessageBus):
    HANDLERS = {
        events.OutOfStock: [allocation.service_layer.handlers.send_out_of_stock_notification],
        events.BatchCreated: [allocation.service_layer.handlers.add_batch],
        events.AllocationRequired: [allocation.service_layer.handlers.allocate],
        events.DeallocationRequired: [allocation.service_layer.handlers.deallocate],
        events.BatchQuantityChanged: [allocation.service_layer.handlers.change_batch_quantity]
    }




