import pytest

from domain import models
from service_layer import services
from adapters.repository import FakeRepository


class FakeSession:
    commited = False

    def commit(self):
        self.commited = True


def test_returns_allocation():
    line = models.OrderLine("o1", "COMPLICATED-LAMP", 10)
    batch = models.Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
    repo = FakeRepository([batch])  # (1)

    result = services.allocate(line, repo, FakeSession())  # (2) (3)
    assert result == "b1"


def test_error_for_invalid_sku():
    line = models.OrderLine("o1", "NONEXISTENTSKU", 10)
    batch = models.Batch("b1", "COMPLICATED-LAMP", 100, eta=None)
    repo = FakeRepository([batch])  # (1)

    with pytest.raises(services.InvalidSku, match="Invalid sku NONEXISTENTSKU"):
        services.allocate(line, repo, FakeSession())


def test_deallocate_decrements_available_quantity():
    repo, session = FakeRepository([]), FakeSession()
    batch = models.Batch("b1", "BLUE-PLINTH", 100, None)
    services.add_batch(batch, repo, session)

    line = models.OrderLine("o1", "BLUE-PLINTH", 10)
    services.allocate(line, repo, session)
    batch = repo.get(reference="b1")
    assert batch.available_quantity == 90

    batch_ref = services.deallocate(
        models.OrderLine("o1", "BLUE-PLINTH", -1), repo, session
    )
    assert batch_ref == "b1"
    assert batch.available_quantity == 100


@pytest.mark.skip(reason="what means correct quantity??")
def test_deallocate_decrements_correct_quantity():
    ...  #  TODO


def test_trying_to_deallocate_unallocated_batch():
    repo, session = FakeRepository([]), FakeSession()
    batch = models.Batch("b1", "BLUE-PLINTH", 100, None)
    services.add_batch(batch, repo, session)

    with pytest.raises(
        models.OrderLineNotFound,
        match="order id o1 sku BLUE-PLINTH not found in batches",
    ):
        batch_ref = services.deallocate(
            models.OrderLine("o1", "BLUE-PLINTH", -1), repo, session
        )
