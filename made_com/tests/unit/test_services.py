import pytest
from datetime import date, timedelta


from service_layer import services, unit_of_work
from adapters.repository import FakeRepository

today = date.today()
tomorrow = today + timedelta(days=1)


class FakeSession:
    commited = False

    def commit(self):
        self.commited = True


def test_add_batch():
    uow = unit_of_work.FakeUnitOfWork()
    services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, uow)
    assert uow.batches.get("b1") is not None
    assert uow.committed


def test_allocate_returns_allocation():
    uow = unit_of_work.FakeUnitOfWork()
    services.add_batch("b1", "COMPLICATED-LAMP", 100, None, uow)

    result = services.allocate("o1", "COMPLICATED-LAMP", 10, uow)  # (2) (3)
    assert result == "b1"


def test_allocate_error_for_invalid_sku():
    uow = unit_of_work.FakeUnitOfWork()
    services.add_batch("b1", "COMPLICATED-LAMP", 100, None, uow)

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, uow)


def test_deallocate_decrements_available_quantity():
    uow = unit_of_work.FakeUnitOfWork()
    services.add_batch("b1", "BLUE-PLINTH", 100, None, uow)

    services.allocate("o1", "BLUE-PLINTH", 10, uow)
    batch = uow.batches.get(reference="b1")
    assert batch.available_quantity == 90

    batch_ref = services.deallocate("o1", "BLUE-PLINTH", -1, uow)
    assert batch_ref == "b1"
    assert batch.available_quantity == 100


@pytest.mark.skip(reason="what means correct quantity??")
def test_deallocate_decrements_correct_quantity():
    ...  #  TODO


def test_trying_to_deallocate_unallocated_batch():
    uow = unit_of_work.FakeUnitOfWork()
    services.add_batch("b1", "BLUE-PLINTH", 100, None, uow)

    with pytest.raises(
        services.OrderLineNotFound,
        match="order id o1 sku BLUE-PLINTH not found in batches",
    ):
        batch_ref = services.deallocate("o1", "BLUE-PLINTH", -1, uow)


def test_prefers_warehouse_batches_to_shipments():
    uow = unit_of_work.FakeUnitOfWork()
    services.add_batch("in-stock-batch", "RETRO-CLOCK", 100, None, uow)
    services.add_batch("shipment-batch", "RETRO-CLOCK", 100, tomorrow, uow)

    services.allocate("ordf", "RETRO-CLOCK", 10, uow)
    assert uow.batches.get("in-stock-batch").available_quantity == 90
    assert uow.batches.get("shipment-batch").available_quantity == 100
