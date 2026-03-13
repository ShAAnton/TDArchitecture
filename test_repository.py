import model
import repository

def test_repository_can_save_a_batch(session):
    batch = model.Batch("batch1", "RUSTY-SOAPDISH", 100, eta=None)

    repo = repository.SQLAlchemyRepository(session)
    repo.add(batch)
    session.commit()

    sql_query = 'SELECT reference, sku, _purchased_quantity, eta FROM batches'
    rows = list(session.execute(sql_query))

    assert rows == [("batch1", "RUSTY-SOAPDISH", 100, None)]

def insert_order_line(session):
    sql_insert = 'INSERT INTO order_lines (order_id, sku, quantity)'\
                 'VALUES ("order1", "GENERIC-SOFA", 12)'
    session.execute(sql_insert)
    sql_query = 'SELECT id FROM order_lines WHERE order_id=:order_id AND sku=:sku'
    [[order_line_id]] = session.execute(sql_query, dict(order_id="order1", sku="GENERIC-SOFA"))

    return order_line_id

def insert_batch(session, batch_id):
    pass

def insert_allocation(session, batch_id, order_line_id):
    pass

def test_repository_can_retrieve_a_batch_with_allocations(session):
    order_line_id = insert_order_line(session)
    batch1_id = insert_batch(session, "batch1")
    insert_batch(session, "batch2")
    insert_allocation(session, batch1_id, order_line_id)

    repo = repository.SQLAlchemyRepository(session)
    retrieved = repo.get("batch1")

    expected = model.Batch("batch1", "GENERIC-SOFA", 100, eta=None)
    assert retrieved == expected # Batch.__eq__ only compares reference
    assert retrieved.sku == expected.sku
    assert retrieved._purchased_quantity == expected._purchased_quantity
    assert retrieved._allocations == {
        model.OrderLine("order1", "GENERIC-SOFA", 12),
    }
