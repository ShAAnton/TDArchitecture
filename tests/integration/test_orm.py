import orm
import model
from datetime import date


def test_order_line_mapper_can_load_lines(session):
    sql_insert = 'INSERT INTO order_lines (order_id, sku, quantity) VALUES '\
            '("order1", "RED-CHAIR", 12), '\
            '("order1", "RED-TABLE", 13), '\
            '("order2", "BLUE-LIPSTICK", 14) '
    session.execute(statement=sql_insert)
    expected = [
        model.OrderLine("order1", "RED-CHAIR", 12),
        model.OrderLine("order1", "RED-TABLE", 13),
        model.OrderLine("order2", "BLUE-LIPSTICK", 14)
    ]
    assert session.query(model.OrderLine).all() == expected

def test_order_line_mapper_can_save_lines(session):
    new_line = model.OrderLine("order1", "DECORATIVE-WIDGET", 12)
    session.add(new_line)
    session.commit()

    select_order_line = "SELECT order_id, sku, quantity FROM order_lines"
    rows = list(session.execute(select_order_line))
    assert rows == [("order1", "DECORATIVE-WIDGET", 12)]

def test_retrieving_batches(session):
    sql_insert = "INSERT INTO batches (reference, sku, _purchased_quantity, eta) "\
                 'VALUES ("batch1", "sku1", 100, null)'
    session.execute(sql_insert)
    sql_insert = "INSERT INTO batches (reference, sku, _purchased_quantity, eta) "\
                 'VALUES ("batch2", "sku2", 200, "2011-04-11") '
    session.execute(sql_insert)
    expected = [
        model.Batch("batch1", "sku1", 100, eta=None),
        model.Batch("batch2", "sku2", 200, eta=date(2011, 4, 11)),
    ]

    assert session.query(model.Batch).all() == expected


def test_saving_batches(session):
    batch = model.Batch("batch1", "sku1", 100, eta=None)
    session.add(batch)
    session.commit()
    sql_query = 'SELECT reference, sku, _purchased_quantity, eta FROM "batches"'
    rows = session.execute(sql_query)
    assert list(rows) == [("batch1", "sku1", 100, None)]


def test_saving_allocations(session):
    batch = model.Batch("batch1", "sku1", 100, eta=None)
    line = model.OrderLine("order1", "sku1", 10)
    batch.allocate(line)
    session.add(batch)
    session.commit()
    sql_query = 'SELECT order_line_id, batch_id FROM "allocations"'
    rows = list(session.execute(sql_query))
    assert rows == [(line.id, batch.id)]


def test_retrieving_allocations(session):
    sql_insert = 'INSERT INTO order_lines (order_id, sku, quantity) VALUES ("order1", "sku1", 12)'
    session.execute(sql_insert)
    sql_query = "SELECT id FROM order_lines WHERE order_id=:order_id AND sku=:sku"
    [[olid]] = session.execute(
        sql_query,
        dict(order_id="order1", sku="sku1"),
    )
    sql_insert = "INSERT INTO batches (reference, sku, _purchased_quantity, eta) "\
                 'VALUES ("batch1", "sku1", 100, null) '
    session.execute(sql_insert)
    sql_query = "SELECT id FROM batches WHERE reference=:ref AND sku=:sku"
    [[bid]] = session.execute(
        sql_query,
        dict(ref="batch1", sku="sku1"),
    )
    sql_insert = "INSERT INTO allocations (order_line_id, batch_id) VALUES (:olid, :bid)"
    session.execute(
        sql_insert,
        dict(olid=olid, bid=bid)
    )

    batch = session.query(model.Batch).one()

    assert batch._allocations == {model.OrderLine("order1", "sku1", 12)}