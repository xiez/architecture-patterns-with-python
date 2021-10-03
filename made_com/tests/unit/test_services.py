import pytest
from datetime import date, timedelta


from service_layer import services
from adapters.repository import FakeRepository

today = date.today()
tomorrow = today + timedelta(days=1)


class FakeSession:
    commited = False

    def commit(self):
        self.commited = True


def test_add_batch():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "CRUNCHY-ARMCHAIR", 100, None, repo, session)
    assert repo.get("b1") is not None
    assert session.commited


def test_allocate_returns_allocation():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "COMPLICATED-LAMP", 100, None, repo, session)

    result = services.allocate("o1", "COMPLICATED-LAMP", 10, repo, session)  # (2) (3)
    assert result == "b1"


def test_allocate_error_for_invalid_sku():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "COMPLICATED-LAMP", 100, None, repo, session)

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate("o1", "NONEXISTENTSKU", 10, repo, session)


def test_deallocate_decrements_available_quantity():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "BLUE-PLINTH", 100, None, repo, session)

    services.allocate("o1", "BLUE-PLINTH", 10, repo, session)
    batch = repo.get(reference="b1")
    assert batch.available_quantity == 90

    batch_ref = services.deallocate("o1", "BLUE-PLINTH", -1, repo, session)
    assert batch_ref == "b1"
    assert batch.available_quantity == 100


@pytest.mark.skip(reason="what means correct quantity??")
def test_deallocate_decrements_correct_quantity():
    ...  #  TODO


def test_trying_to_deallocate_unallocated_batch():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("b1", "BLUE-PLINTH", 100, None, repo, session)

    with pytest.raises(
        services.OrderLineNotFound,
        match="order id o1 sku BLUE-PLINTH not found in batches",
    ):
        batch_ref = services.deallocate("o1", "BLUE-PLINTH", -1, repo, session)


def test_prefers_warehouse_batches_to_shipments():
    repo, session = FakeRepository([]), FakeSession()
    services.add_batch("in-stock-batch", "RETRO-CLOCK", 100, None, repo, session)
    services.add_batch("shipment-batch", "RETRO-CLOCK", 100, tomorrow, repo, session)

    services.allocate("ordf", "RETRO-CLOCK", 10, repo, session)
    assert repo.get("in-stock-batch").available_quantity == 90
    assert repo.get("shipment-batch").available_quantity == 100
