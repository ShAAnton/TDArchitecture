from typing import Dict, Type, List, Callable, Union
from allocation.domain import events, commands
import allocation.service_layer.handlers
from allocation.service_layer.unit_of_work import AbstractionUnitOfWork
import logging

Message = Union[events.Event, commands.Command]

class AbstractionMessageBus:
    HANDLERS: Dict[Type[events.Event], List[Callable]]

    def __init__(self, uow: AbstractionUnitOfWork):
        self.uow = uow

    def handle(self, message: Message):
        results, queue = list(), [event]
        while queue:
            message = queue.pop(0)
            if isinstance(message, events.Event):
                self.handle_event(event, queue, self.uow)
            elif isinstance(message, commands.Command):
                cmd_result = self.handle_command(message, queue, uow=self.uow)
            else:
                raise TypeError(f'{message} was not an Event or Command')
        return results

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
            result = handler(command, uow=uow)
            queue.extend(uow.collect_new_events())
            return result
        except Exception:
            logger.exception('Exception handling command %s', command)
            raise


class MessageBus(AbstractionMessageBus):
    EVENT_HANDLERS = {
        events.OutOfStock: [allocation.service_layer.handlers.send_out_of_stock_notification],
    }
    COMMAND_HANDLERS = {
        commands.CreateBatch: [allocation.service_layer.handlers.add_batch],
        commands.Allocate: [allocation.service_layer.handlers.allocate],
        commands.Deallocate: [allocation.service_layer.handlers.deallocate],
        commands.ChangeBatchQuantity: [allocation.service_layer.handlers.change_batch_quantity]
    }




