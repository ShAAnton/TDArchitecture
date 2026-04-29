from allocation.service_layer import unit_of_work
from allocation.domain import model

# def allocations(order_id: str, uow: unit_of_work.SqlAlchemyUnitOfWork):
#     with uow:
#         results = list(
#             uow.session.execute(
#                 'SELECT ol.sku, b.reference'
#                 ' FROM allocations AS a'
#                 ' JOIN batches AS b ON a.batch_id = b.id'
#                 ' JOIN order_lines AS ol ON a.order_line_id = ol.id'
#                 ' WHERE ol.order_id = :order_id',
#                 dict(order_id=order_id)
#             )
#         )
#         return [
#             {'sku': sku, 'batch_ref': reference} for sku, reference in results
#         ]

# def allocations(order_id: str, uow: unit_of_work.SqlAlchemyUnitOfWork):
#     with uow:
#         batches = uow.session.query(model.Batch).join(
#             model.OrderLine, model.Batch._allocations
#         ).filter(
#             model.OrderLine.order_id == order_id
#         )
#         return [
#             {"sku": b.sku,
#              "batch_ref": b.reference}
#             for b in batches
#         ]


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
