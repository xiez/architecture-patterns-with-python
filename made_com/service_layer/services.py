from typing import Optional
from datetime import date

from domain import models
from domain.models import OrderLine, Batch
from adapters.repository import AbstractRepository
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
        batches = uow.batches.list()
        if not is_valid_sku(line.sku, batches):
            raise InvalidSku(f"Invalid sku {line.sku}")
        batchref = models.allocate(line, batches)
        uow.commit()
    return batchref


def deallocate(orderid: str, sku: str, qty: int, uow: AbstractUnitOfWork) -> str:
    line = OrderLine(orderid, sku, qty)
    with uow:
        batches = uow.batches.list()
        if not is_valid_sku(line.sku, batches):
            raise InvalidSku(f"Invalid sku {line.sku}")
        try:
            batchref = models.deallocate(line, batches)
            uow.commit()
            return batchref
        except models.OrderLineNotFound as e:
            raise OrderLineNotFound(str(e))


def add_batch(
    ref: str, sku: str, qty: int, eta: Optional[date], uow: AbstractUnitOfWork
) -> None:
    with uow:
        uow.batches.add(Batch(ref, sku, qty, eta))
        uow.commit()
