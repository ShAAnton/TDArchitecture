from allocation.domain import model
from allocation.adapters import repository


def insert_and_return_order_line(session):
    order_line = model.OrderLine("order1", "GENERIC-SOFA", 12)
    sql_insert = 'INSERT INTO order_lines (order_id, sku, quantity)'\
                 f'VALUES ("{order_line.order_id}", "{order_line.sku}", {order_line.quantity})'
    session.execute(sql_insert)
    sql_query = 'SELECT id FROM order_lines WHERE order_id=:order_id AND sku=:sku'
    [[order_line_id]] = session.execute(
        sql_query,
        dict(order_id=order_line.order_id, sku=order_line.sku)
    )

    return order_line_id, order_line


def insert_and_return_batch(session, batch_id):
    batch = model.Batch(batch_id, "GENERIC-SOFA", 100, eta=None)
    sql_insert = 'INSERT INTO batches (reference, _purchased_quantity, sku, eta) '\
            f'VALUES ("{batch.reference}", {batch._purchased_quantity}, "{batch.sku}", {batch.eta or 'null'})'
    session.execute(sql_insert)
    sql_query = 'SELECT id FROM batches WHERE reference=:reference'
    [[batch_id]] = session.execute(sql_query, dict(reference=batch.reference))
    return batch_id, batch


def insert_allocation(session, batch_id, order_line_id):
    sql_insert = 'INSERT INTO allocations (batch_id, order_line_id)'\
                 f'VALUES ("{batch_id}", "{order_line_id}")'
    session.execute(sql_insert)


def test_repository_can_save_a_batch(session):
    batch = model.Batch("batch1", "RUSTY-SOAPDISH", 100, eta=None)

    repo = repository.SQLAlchemyRepository(session)
    repo.add(batch)
    session.commit()

    sql_query = 'SELECT reference, sku, _purchased_quantity, eta FROM batches'
    rows = session.execute(sql_query)
    rows = list(rows)

    assert rows == [("batch1", "RUSTY-SOAPDISH", 100, None)]


def get_allocations(session, batch_id):
    sql_select = ("SELECT order_id "
                  "FROM allocations "
                  "JOIN order_lines ON order_lines.id = allocations.order_line_id "
                  "JOIN batches ON batches.id = allocations.batch_id "
                  "WHERE batches.reference = :batch_id ")
    rows = list(
        session.execute(
            sql_select,
            dict(batch_id=batch_id)
        )
    )

    return {row[0] for row in rows}

def test_repository_can_retrieve_a_batch_with_allocations(session):
    order_line_id, order_line = insert_and_return_order_line(session)
    batch1_id, batch1 = insert_and_return_batch(session, "batch1")
    insert_and_return_batch(session, "batch2")
    insert_allocation(session, batch1_id, order_line_id)

    repo = repository.SQLAlchemyRepository(session)
    retrieved = repo.get("batch1")

    expected = batch1
    assert retrieved == expected # Batch.__eq__ only compares reference
    assert retrieved.sku == expected.sku
    assert retrieved._purchased_quantity == expected._purchased_quantity
    assert retrieved._allocations == {
        order_line,
    }

def test_updating_a_batch(session):
    sku = "WEATHERED-BENCH"
    order1 = model.OrderLine("order1", sku, 10)
    order2 = model.OrderLine("order2", sku, 20)
    batch = model.Batch("batch1", sku, 100, eta=None)
    repo = repository.SQLAlchemyRepository(session)

    batch.allocate(order1)
    repo.add(batch)
    session.commit()

    batch.allocate(order2)
    repo.add(batch)
    session.commit()

    assert get_allocations(session, "batch1") == {"order1", "order2"}