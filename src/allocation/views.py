from allocation.service_layer import unit_of_work


def allocations(order_id: str, uow: unit_of_work.SqlAlchemyUnitOfWork):
    with uow:
        results = list(
            uow.session.execute(
                'SELECT ol.sku, b.reference'
                ' FROM allocations AS a'
                ' JOIN batches AS b ON a.batch_id = b.id'
                ' JOIN order_lines AS ol ON a.order_line_id = ol.id'
                ' WHERE ol.order_id = :order_id',
                dict(order_id=order_id)
            )
        )
        return [
            {'sku': sku, 'batch_ref': reference} for sku, reference in results
        ]