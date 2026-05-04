from typing import Dict, Type, List, Callable, Union
from allocation.domain import events, commands
import allocation.service_layer.handlers as handlers
from allocation.service_layer.unit_of_work import AbstractionUnitOfWork
import logging

logger = logging.getLogger(__name__)
Message = Union[events.Event, commands.Command]

class AbstractionMessageBus:
    EVENT_HANDLERS: Dict[Type[events.Event], List[Callable]]
    COMMAND_HANDLERS: Dict[Type[commands.Command], Callable]


    def __init__(self, uow: AbstractionUnitOfWork):
        self.uow = uow

    def handle(self, message: Message):
        queue = [message]
        while queue:
            message = queue.pop(0)

            if isinstance(message, events.Event):
                self.handle_event(message, queue, self.uow)
            elif isinstance(message, commands.Command):
                self.handle_command(message, queue, uow=self.uow)
            else:
                raise TypeError(f'{message} was not an Event or Command')

    def handle_event(
                self,
                event: events.Event,
                queue: List[Message],
                uow: AbstractionUnitOfWork
            ):
        for handler in self.EVENT_HANDLERS[type(event)]:
            try:
                logger.debug('handling event %s with handler %s', event, handler)
                handler(event, uow=uow)
                queue.extend(uow.collect_new_events())
            except Exception:
                logger.exception('Exception handling event %s', event)
                continue


    def handle_command(
            self,
            command: commands.Command,
            queue: List[Message],
            uow: AbstractionUnitOfWork
    ):
        logger.debug('handling command %s', command)
        try:
            handler = self.COMMAND_HANDLERS[type(command)]
            handler(command, uow=uow)
            queue.extend(uow.collect_new_events())
        except Exception:
            logger.exception('Exception handling command %s', command)
            raise


class MessageBus(AbstractionMessageBus):
    EVENT_HANDLERS = {
        events.Allocated: [
            handlers.publish_allocated_event,
            handlers.add_allocation_to_read_model,
        ],
        events.Deallocated: [
            # handlers.reallocate,
            handlers.remove_allocation_from_read_model
        ],
        events.OutOfStock: [
            handlers.send_out_of_stock_notification
        ],
    }
    COMMAND_HANDLERS = {
        commands.CreateBatch: handlers.add_batch,
        commands.Allocate: handlers.allocate,
        commands.Deallocate: handlers.deallocate,
        commands.Reallocate: handlers.reallocate,
        commands.ChangeBatchQuantity: handlers.change_batch_quantity,
    }




