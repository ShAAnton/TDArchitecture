from allocation.service_layer import unit_of_work, message_bus
from allocation.domain import commands
from allocation import views
from datetime import date

today = date.today()


def test_allocations_view(sqlite_session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
    mb = message_bus.MessageBus(uow)
    mb.handle(commands.CreateBatch('sku1batch', 'sku1', 50, None))
    mb.handle(commands.CreateBatch('sku2batch', 'sku2', 50, today))
    mb.handle(commands.Allocate('order1', 'sku1', 20))
    mb.handle(commands.Allocate('order1', 'sku2', 20))
    # add a spurious batch and order to make sure we are getting the right one
    mb.handle(commands.CreateBatch('sku1batch-later', 'sku1', 50, today))
    mb.handle(commands.Allocate('otherorder', 'sku1', 30))
    mb.handle(commands.Allocate('otherorder', 'sku2', 10))

    assert views.allocations('order1', uow) == [
        {'sku': 'sku1', 'batch_ref': 'sku1batch'},
        {'sku': 'sku2', 'batch_ref': 'sku2batch'},
    ]


def test_deallocation(sqlite_session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(sqlite_session_factory)
    mb = message_bus.MessageBus(uow)
    mb.handle(commands.CreateBatch("b1", "sku1", 50, None))
    mb.handle(commands.CreateBatch("b2", "sku1", 50, today))
    mb.handle(commands.Allocate("o1", "sku1", 40))
    mb.handle(commands.ChangeBatchQuantity("b1", 10))

    assert views.allocations("o1", uow) == [
        {"sku": "sku1", "batch_ref": "b2"},
    ]