from dataclasses import dataclass
from typing import *
from datetime import date
import allocation.domain.events as events


class OutOfStock(Exception):
    pass

class NotAllocatedLine(Exception):
    pass

@dataclass(unsafe_hash=True)
class OrderLine:
    order_id: str
    sku: str
    quantity: int


class Batch:
    def __init__(
            self, ref: str, sku: str, quantity: int, eta: Optional[date]
    ):
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = quantity
        self._allocations: Set[OrderLine] = set()

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def can_allocate(self, line: OrderLine):
        return self.sku == line.sku and self.available_quantity >= line.quantity

    def deallocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)

    def can_deallocate(self, line: OrderLine):
        return line in self._allocations

    def deallocate_one(self):
        return self._allocations.pop()

    @property
    def allocated_quantity(self) -> int:
        return sum(line.quantity for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_quantity

    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta

    def __eq__(self, other):
        return isinstance(other, Batch) and self.reference == other.reference

    def __hash__(self):
        return hash(self.reference)


class Product:
    def __init__(self, sku: str, batches: List[Batch], version_number=1):
        self.sku = sku
        self.batches = batches
        self.version_number = version_number
        self.events = list()

    def allocate(self, line: OrderLine) -> str:
        allocated_batch_ref = None
        try:
            batch = next(
                b for b in sorted(self.batches) if b.can_allocate(line)
            )
            batch.allocate(line)
            self.version_number += 1
            allocated_batch_ref = batch.reference
        except StopIteration:
            self.events.append(events.OutOfStock(line.sku))
        return allocated_batch_ref

    def deallocate(self, line: OrderLine) -> str:
        allocated_batch_ref = None
        try:
            batch = next(
                b for b in sorted(self.batches) if b.can_deallocate(line)
            )
            batch.deallocate(line)
            self.version_number += 1
            allocated_batch_ref = batch.reference
        except StopIteration:
            self.events.append(events.NotAllocatedLine(line.sku))
        return allocated_batch_ref

    def change_batch_quantity(self, batch_ref, quantity):
        batch  = next(
            b for b in self.batches if b.reference == batch_ref
        )
        batch._purchased_quantity = quantity
        while batch.available_quantity < 0:
            line = batch.deallocate_one()
            self.events.append(
                events.AllocationRequired(line.order_id, line.sku, line.quantity)
            )