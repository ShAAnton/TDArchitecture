from typing import Dict, Type, List, Callable
import allocation.domain.events as events

def handle(event: events.Event):
    for handler in HANDLERS[type(event)]:
        handler(event)

def send_out_of_stock_notification(event: events.OutOfStock):
    # email.send_mail(
    #     'stock@made.com',
    #     f'Out of stock for {event.sku}'
    # )
    ...

HANDLERS: Dict[Type[events.Event], List[Callable]] = {
    events.OutOfStock: [send_out_of_stock_notification]
}