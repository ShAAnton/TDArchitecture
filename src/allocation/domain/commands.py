from dataclasses import dataclass
from typing import Optional
from datetime import date


class Command:
    pass

@dataclass
class Allocate(Command):
    order_id: str
    sku: str
    quantity: int

@dataclass
class CreateBatch(Command):
    reference: str
    sku: str
    quantity: int
    eta: Optional[date] = None

@dataclass
class ChangeBatchQuantity(Command):
    reference: str
    quantity: int

@dataclass
class Deallocate(Command):
    order_id: str
    sku: str
    quantity: int