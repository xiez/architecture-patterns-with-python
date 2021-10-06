from dataclasses import dataclass
from typing import Optional, Set, List
from datetime import date


class OutOfStock(Exception):
    pass


class OrderLineNotFound(Exception):
    pass


@dataclass(unsafe_hash=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int


class Batch:
    def __init__(self, ref: str, sku: str, qty: int, eta: Optional[date]):
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations = set()  # type: Set[OrderLine]

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line):
        if line in self._allocations:
            self._allocations.remove(line)

    @property
    def allocated_quantity(self):
        return sum([line.qty for line in self._allocations])

    @property
    def available_quantity(self):
        return self._purchased_quantity - self.allocated_quantity

    def can_allocate(self, line):
        return self.sku == line.sku and self.available_quantity >= line.qty

    def find_allocation(self, line):
        for e in self._allocations:
            if line.orderid == e.orderid and line.sku == e.sku:
                return e

    def __eq__(self, other):
        if not isinstance(other, Batch):
            return False

        return other.reference == self.reference

    def __hash__(self):
        return hash(self.reference)

    def __gt__(self, other):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta


class Product:
    def __init__(self, sku: str, batches: List[Batch], version_number: int = 0):
        self.sku = sku
        self.batches = batches
        self.version_number = version_number

    def allocate(self, line: OrderLine) -> str:
        try:
            batch = next(b for b in sorted(self.batches) if b.can_allocate(line))
            batch.allocate(line)
            self.version_number += 1
            return batch.reference
        except StopIteration:
            raise OutOfStock(f"Out of stock for sku {line.sku}")

    def deallocate(self, line) -> str:
        find = False
        for b in sorted(self.batches):
            a_line = b.find_allocation(line)
            if a_line:
                b.deallocate(a_line)
                self.version_number += 1
                return b.reference

        if not find:
            raise OrderLineNotFound(
                f"order id {line.orderid} sku {line.sku} not found in batches"
            )


def allocate(line, batches) -> str:
    try:
        batch = next(b for b in sorted(batches) if b.can_allocate(line))
        batch.allocate(line)
        return batch.reference
    except StopIteration:
        raise OutOfStock(f"Out of stock for sku {line.sku}")


def deallocate(line, batches) -> str:
    find = False
    for b in sorted(batches):
        a_line = b.find_allocation(line)
        if a_line:
            b.deallocate(a_line)
            return b.reference

    if not find:
        raise OrderLineNotFound(
            f"order id {line.orderid} sku {line.sku} not found in batches"
        )
