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
class BatchCreated(Event):
    batch_ref: str
    sku: str
    quantity: int
    eta: Optional[date] = None

@dataclass
class AllocationRequired(Event):
    order_id: str
    sku: str
    quantity: int

@dataclass
class DeallocationRequired(Event):
    order_id: str
    sku: str
    quantity: int


@dataclass
class AllocationRequest:
    order1: str
    sku: str
    quantity: int

@dataclass
class BatchQuantityChanged:
    batch_ref: str
    quantity: int