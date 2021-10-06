from typing import Optional
from datetime import date

from domain import models
from domain.models import OrderLine, Batch
from service_layer.unit_of_work import AbstractUnitOfWork


class InvalidSku(Exception):
    pass


class OrderLineNotFound(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def allocate(orderid: str, sku: str, qty: int, uow: AbstractUnitOfWork) -> str:
    line = OrderLine(orderid, sku, qty)
    with uow:
        product = uow.products.get(sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = product.allocate(line)
        uow.commit()
    return batchref


def deallocate(orderid: str, sku: str, qty: int, uow: AbstractUnitOfWork) -> str:
    line = OrderLine(orderid, sku, qty)
    with uow:
        product = uow.products.get(sku)
        if product is None:
            raise InvalidSku(f"Invalid sku {line.sku}")
        try:
            batchref = product.deallocate(line)
            uow.commit()
            return batchref
        except models.OrderLineNotFound as e:
            raise OrderLineNotFound(str(e))


def add_batch(
    ref: str, sku: str, qty: int, eta: Optional[date], uow: AbstractUnitOfWork
) -> None:
    with uow:
        product = uow.products.get(sku)
        if product is None:
            product = models.Product(sku, batches=[])
            uow.products.add(product)
        product.batches.append(Batch(ref, sku, qty, eta))
        uow.commit()
