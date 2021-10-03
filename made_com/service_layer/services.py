from typing import Optional
from datetime import date

from domain import models
from domain.models import OrderLine, Batch
from adapters.repository import AbstractRepository


class InvalidSku(Exception):
    pass


class OrderLineNotFound(Exception):
    pass


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


def allocate(
    orderid: str, sku: str, qty: int, repo: AbstractRepository, session
) -> str:
    line = OrderLine(orderid, sku, qty)
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku {line.sku}")
    batchref = models.allocate(line, batches)
    session.commit()
    return batchref


def deallocate(
    orderid: str, sku: str, qty: int, repo: AbstractRepository, session
) -> str:
    line = OrderLine(orderid, sku, qty)
    batches = repo.list()
    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f"Invalid sku {line.sku}")
    try:
        batchref = models.deallocate(line, batches)
        session.commit()
        return batchref
    except models.OrderLineNotFound as e:
        raise OrderLineNotFound(str(e))


def add_batch(ref: str, sku: str, qty: int, eta: Optional[date], repo, session) -> None:
    batch = Batch(ref, sku, qty, eta)
    repo.add(batch)
    session.commit()
