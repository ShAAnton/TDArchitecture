import inspect
from typing import Callable
from allocation.service_layer import unit_of_work, message_bus
from allocation.adapters import email, redis_eventpublisher, orm
from allocation.service_layer import handlers

def bootstrap(
        start_orm: bool = True,
        uow: unit_of_work.AbstractionUnitOfWork = unit_of_work.SqlAlchemyUnitOfWork(),
        send_mail: Callable = email.send_email,
        publish: Callable = redis_eventpublisher.publish,
)-> message_bus.MessageBus:

    if start_orm:
        orm.start_mappers()

    dependencies = {'uow': uow, 'send_mail': send_mail, 'publish': publish}
    injected_event_handlers = {
        event_type: [
            inject_dependencies(handler, dependencies)
            for handler in event_handlers
        ]
        for event_type, event_handlers in handlers.EVENT_HANDLERS.items()
    }
    inject_command_handlers = {
        command_type: inject_dependencies(command_handler, dependencies)
        for command_type, command_handler in handlers.COMMAND_HANDLERS.items()
    }

    return message_bus.MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=inject_command_handlers,
    )

def inject_dependencies(handler, dependencies):
    params = inspect.signature(handler).parameters
    injection = {
        name: dependency
        for name, dependency in dependencies.items()
        if name in params
    }
    if inspect.isclass(handler):
        print(f"inject into class {type(handler)}")
        return handler(**injection)
    elif inspect.isfunction(handler):
        print(f"inject into function {type(handler)}")
        return lambda message: handler(message, **injection)
    raise TypeError()