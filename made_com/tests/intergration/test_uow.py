import threading
import traceback
import time
import pytest

from domain import models
from service_layer import unit_of_work
from tests.utils import random_sku, random_orderid, random_batchref


def insert_batch(session, ref, sku, qty, eta, product_version=1):
    session.execute(
        "INSERT INTO products (sku, version_number) VALUES (:sku, :version)",
        dict(sku=sku, version=product_version),
    )
    session.execute(
        "INSERT INTO batches (reference, sku, _purchased_quantity, eta)"
        " VALUES (:ref, :sku, :qty, :eta)",
        dict(ref=ref, sku=sku, qty=qty, eta=eta),
    )


def get_allocated_batch_ref(session, orderid, sku):
    pass


# def test_uow_can_retrieve_a_batch_and_allocate_to_it(session_factory):
#     session = session_factory()
#     insert_batch()


def test_rolls_back_uncommited_work_by_default(session_factory):
    uow = unit_of_work.SqlalchemyUnitOfWork(session_factory)
    with uow:
        insert_batch(uow.session, "batch1", "MEDIUM-PLINTH", 100, None)

    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM "batches"'))
    assert rows == []


def test_rolls_back_on_error(session_factory):
    class MyException(Exception):
        pass

    uow = unit_of_work.SqlalchemyUnitOfWork(session_factory)
    with pytest.raises(MyException):
        with uow:
            insert_batch(uow.session, "batch1", "MEDIUM-PLINTH", 100, None)
            raise MyException()

    new_session = session_factory()
    rows = list(new_session.execute('SELECT * FROM "batches"'))
    assert rows == []


def test_concurrent_updates_to_version_are_not_allowed(postgres_session_factory):
    def try_to_allocate(orderid, sku, exceptions):
        line = models.OrderLine(orderid, sku, 10)
        try:
            with unit_of_work.SqlalchemyUnitOfWork() as uow:
                product = uow.products.get(sku=sku)
                product.allocate(line)
                time.sleep(0.2)
                uow.commit()
        except Exception as e:
            # print(traceback.format_exc())
            exceptions.append(e)

    sku, batch = random_sku(), random_batchref()
    session = postgres_session_factory()
    insert_batch(session, batch, sku, 100, eta=None, product_version=1)

    session.commit()

    order1, order2 = random_orderid(1), random_orderid(2)
    exceptions = []  # type: List[Exception]

    try_to_allocate_order1 = lambda: try_to_allocate(order1, sku, exceptions)
    try_to_allocate_order2 = lambda: try_to_allocate(order2, sku, exceptions)
    thread1 = threading.Thread(target=try_to_allocate_order1)
    thread2 = threading.Thread(target=try_to_allocate_order2)
    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

    [[version]] = session.execute(
        "SELECT version_number FROM products WHERE sku=:sku",
        dict(sku=sku),
    )
    assert version == 2
    [exception] = exceptions
    assert "could not serialize access due to concurrent update" in str(exception)

    orders = session.execute(
        "SELECT orderid FROM allocations"
        " JOIN batches ON allocations.batch_id = batches.id"
        " JOIN order_lines ON allocations.orderline_id = order_lines.id"
        " WHERE order_lines.sku=:sku",
        dict(sku=sku),
    )
    assert orders.rowcount == 1
    with unit_of_work.SqlalchemyUnitOfWork() as uow:
        uow.session.execute("select 1")
