import allocation.service_layer.unit_of_work as unit_of_work
import pytest

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

def test_roll_back_uncommitted_work_by_default(session_factory):
    uow = unit_of_work.SqlAlchemyUnitOfWork(session_factory)
    with uow:
        insert_batch(uow.session, "batch1", "MEDIUM-PLINTH", 100, None)

    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM batches'))
    assert rows == []

def test_roll_back_on_error(session_factory):
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