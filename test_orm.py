import orm
import model


def test_orderline_mapper_can_load_lines(session):
    bulk_insert = orm.text(
        'INSERT INTO order_lines (order_id, sku, quantity) VALUES'
            '("order1", "RED-CHAIR", 12),'
            '("order1", "RED-TABLE", 13),'
            '("order2", "BLUE-LIPSTICK", 14)')
    session.execute(bulk_insert)
    expected = [
        model.OrderLine("order1", "RED-CHAIR", 12),
        model.OrderLine("order1", "RED-TABLE", 13),
        model.OrderLine("order2", "BLUE-LIPSTICK", 14)
    ]
    assert session.query(model.OrderLine).all() == expected

def test_orderline_mapper_can_save_lines(session):
    new_line = model.OrderLine("order1", "DECORATIVE-WIDGET", 12)
    session.add(new_line)
    session.commit()


    select_order_line = orm.text("SELECT order_id, sku, quantity FROM order_lines")
    rows = list(session.execute(select_order_line))
    assert rows == [("order1", "DECORATIVE-WIDGET", 12)]
