from sqlalchemy import *
from sqlalchemy import orm
from sqlalchemy.orm import relationship

from allocation.domain import model


class Session(orm.Session):
    def execute(self, *args, **kwargs):
        if isinstance(kwargs.get('statement'), str):
            kwargs['statement'] = text(kwargs['statement'])
        elif kwargs.get('statement') is None and len(args) > 0 and isinstance(args[0], str):
            args = list(args)
            args[0] = text(args[0])
        return super().execute(*args, **kwargs)


def sessionmaker(*args, **kwargs):
    if kwargs.get('class_') is None:
        kwargs['class_'] = Session
    return orm.sessionmaker(*args, **kwargs)


metadata = MetaData()

order_lines = Table(
    'order_lines', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('sku', String(255)),
    Column('quantity', Integer, nullable=False),
    Column('order_id', String(255))
)

products = Table(
    "products",
    metadata,
    Column("sku", String(255), primary_key=True)
)

batches = Table(
    'batches', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('reference', String(255)),
    Column('sku', ForeignKey("products.sku")),
    Column('_purchased_quantity', Integer, nullable=False),
    Column('eta', Date, nullable=True)
)

allocations = Table(
    "allocations", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("batch_id", ForeignKey("batches.id")),
    Column("order_line_id", ForeignKey("order_lines.id"))
)

def start_mappers():
    mapper_registry = orm.registry()
    lines_mapper = mapper_registry.map_imperatively(model.OrderLine, order_lines)
    batches_mapper = mapper_registry.map_imperatively(
        model.Batch,
        batches,
        properties={
            "_allocations": orm.relationship(
                lines_mapper,
                secondary=allocations,
                collection_class=set,
            )
        },
    )
    mapper_registry.map_imperatively(
        model.Product,
        products,
        properties={
            "batches": relationship(batches_mapper)
        }
    )
