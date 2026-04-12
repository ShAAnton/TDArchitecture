from typing import Dict, Type, List, Callable
import allocation.domain.events as events
import allocation.service_layer.handlers
from allocation.service_layer.unit_of_work import AbstractionUnitOfWork


def handle(events_: List[events.Event], uow: AbstractionUnitOfWork):
    results = []
    while events_:
        event = events_.pop(0)
        print('handling message', event)
        for handler in HANDLERS[type(event)]:
            r = handler(event, uow)
            print('got result', r)
            results.append(r)
    return results


HANDLERS: Dict[Type[events.Event], List[Callable]] = {
    events.OutOfStock: [allocation.service_layer.handlers.send_out_of_stock_notification],
    events.BatchCreated: [allocation.service_layer.handlers.add_batch],
    events.AllocationRequired: [allocation.service_layer.handlers.allocate],
    events.DeallocationRequired: [allocation.service_layer.handlers.deallocate]
}