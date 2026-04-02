import traceback
import threading
import allocation.service_layer.unit_of_work as unit_of_work
import pytest
import allocation.domain.model as model
from allocation.service_layer.unit_of_work import SqlAlchemyUnitOfWork
import time
from ..random_refs import random_sku, random_batch_ref, random_order_id



def insert_batch(session, reference, sku, quantity, eta):
    sql_insert = ('INSERT INTO batches '
                  '(reference, _purchased_quantity, sku, eta) '
                  'VALUES (:reference, :quantity, :sku, :eta) '
                  )
    batch_param = dict(reference=reference,
                       quantity=quantity,
                       sku=sku,
                       eta=eta)
    session.execute(sql_insert, batch_param)

def get_allocated_batch_ref(session, order_id, sku):
    sql_select = ('SELECT id '
                  'FROM order_lines '
                  'WHERE order_id = :order_id '
                  'AND sku=:sku ')
    sql_param = dict(order_id=order_id, sku=sku)
    [[order_line_id]] = session.execute(sql_select, sql_param)
    sql_select = ('SELECT b.reference '
                  'FROM allocations '
                  'JOIN batches AS b '
                  'ON batch_id = b.id '
                  'WHERE order_line_id = :order_line_id')
    sql_param = dict(order_line_id=order_line_id)
    [[batch_ref]] = session.execute(sql_select, sql_param)
    return batch_ref

def test_uow_can_retrieve_a_batch_and_allocate_to_it(session_factory):
    sku = 'HIPSTER-WORKBENCH'
    session = session_factory()
    insert_batch(session, 'batch1', sku, 100, None)
    session.commit()

    uow = SqlAlchemyUnitOfWork(session_factory)
    with uow:
        batch = uow.batches.get('batch1')
        order_id = 'o1'
        line = model.OrderLine(order_id, sku, 10)
        batch.allocate(line)
        uow.commit()

    batch_ref = get_allocated_batch_ref(session, order_id, sku)
    assert batch_ref == 'batch1'

def test_rolls_back_uncommitted_work_by_default(session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        insert_batch(uow.session, "batch1", "MEDIUM-PLINTH", 100, None)

    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM batches'))
    assert rows == []

def test_rolls_back_on_error(session_factory):
    class MyException(Exception):
        pass

    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with pytest.raises(MyException):
        with uow:
            insert_batch(uow.session, 'batch1', 'LARGE-FORK', 100, None)
            raise MyException

    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM batches'))
    assert rows == []

def try_to_allocate(order_id, sku, exceptions):
    line = model.OrderLine(order_id, sku, 10)
    try:
        with unit_of_work.SqlAlchemyUnitOfWork() as uow:
            product = uow.products.get(sku=sku)
            product.allocate(line)
            time.sleep(0.2)
            uow.commit()
    except Exception as e:
        print(traceback.format_exc())
        exceptions.append(e)
