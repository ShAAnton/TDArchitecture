from allocation.service_layer import unit_of_work
from allocation.domain import model


def allocations(order_id: str, uow: unit_of_work.SqlAlchemyUnitOfWork):
    with uow:
        results = list(
            uow.session.execute(
                'SELECT sku, batch_ref'
                ' FROM allocations_view'
                ' WHERE order_id = :order_id',
                dict(order_id=order_id)
            )
        )
        return [
            {'sku': sku, 'batch_ref': batch_ref} for sku, batch_ref in results
        ]
