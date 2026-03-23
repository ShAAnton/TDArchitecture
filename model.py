from dataclasses import dataclass
from typing import *
from datetime import date


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

    def deallocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)
        else:
            raise NotAllocatedLine(f"Can not deallocate not allocated line {line.sku}")

    def can_allocate(self, line: OrderLine):
        return self.sku == line.sku and self.available_quantity >= line.quantity

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


def allocate(line: OrderLine, batches: list[Batch]):
    sorted_batches = sorted(batch for batch in batches if batch.can_allocate(line))
    for batch in sorted_batches:
        if batch.can_allocate(line):
            batch.allocate(line)
            return batch.reference
    raise OutOfStock(f'Out of stock for sku {line.sku}')
