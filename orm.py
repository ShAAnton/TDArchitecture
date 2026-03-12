from sqlalchemy import *
from sqlalchemy import orm

# from sqlalchemy.orm import mapper, relationship
import model

metadata = MetaData()

order_lines = Table(
    'order_lines', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('sku', String(255)),
    Column('quantity', Integer, nullable=False),
    Column('order_id', String(255))
)

def start_mappers():
    mapper_registry = orm.registry()
    lines_mapper = mapper_registry.map_imperatively(model.OrderLine, order_lines)
