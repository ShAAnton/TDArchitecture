from dataclasses import dataclass
from typing import Optional
from datetime import date

class Event:
    pass

@dataclass
class OutOfStock(Event):
    sku: str

@dataclass
class NotAllocatedLine(Event):
    sku: str

@dataclass
class Allocated(Event):
    order_id: str
    sku: str
    quantity: int
    batch_ref: str