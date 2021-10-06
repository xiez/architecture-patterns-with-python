import uuid
import pytest
import requests

import config
from tests.utils import random_suffix, random_sku, random_batchref, random_orderid


@pytest.mark.usefixtures("restart_api")
@pytest.mark.usefixtures("postgres_db")
def test_happy_path_returns_201_and_allocated_batch():
    sku, othersku = random_sku(), random_sku("other")
    earlybatch = random_batchref(1)
    laterbatch = random_batchref(2)
    otherbatch = random_batchref(3)
    post_to_add_batch(laterbatch, sku, 100, "2011-01-02")
    post_to_add_batch(earlybatch, sku, 100, "2011-01-01")
    post_to_add_batch(otherbatch, othersku, 100, None)

    data = {"orderid": random_orderid(), "sku": sku, "qty": 3}
    url = config.get_api_url()

    r = requests.post(f"{url}/allocate", json=data)

    assert r.status_code == 201
    assert r.json()["batchref"] == earlybatch


@pytest.mark.usefixtures("restart_api")
@pytest.mark.usefixtures("postgres_db")
def test_unhappy_path_returns_400_and_error_message():
    unknown_sku, orderid = random_sku(), random_orderid()
    data = {"orderid": orderid, "sku": unknown_sku, "qty": 20}
    url = config.get_api_url()
    r = requests.post(f"{url}/allocate", json=data)
    assert r.status_code == 400
    assert r.json()["message"] == f"Invalid sku {unknown_sku}"


def post_to_add_batch(batchref, sku, qty, eta):
    url = config.get_api_url()
    r = requests.post(
        f"{url}/batches",
        json={"reference": batchref, "sku": sku, "qty": 100, "eta": eta},
    )
    assert r.status_code == 201


@pytest.mark.usefixtures("restart_api")
@pytest.mark.usefixtures("postgres_db")
def test_deallocate():
    sku, order1, order2 = random_sku(), random_orderid(), random_orderid()
    batch = random_batchref()
    post_to_add_batch(batch, sku, 100, "2011-01-02")
    url = config.get_api_url()
    # fully allocate
    r = requests.post(
        f"{url}/allocate", json={"orderid": order1, "sku": sku, "qty": 100}
    )
    assert r.json()["batchref"] == batch

    # cannot allocate second order
    r = requests.post(
        f"{url}/allocate", json={"orderid": order2, "sku": sku, "qty": 100}
    )
    assert r.status_code == 400
    assert r.json()["message"] == f"Out of stock for sku {sku}"

    # deallocate
    r = requests.post(
        f"{url}/deallocate",
        json={
            "orderid": order1,
            "sku": sku,
        },
    )
    assert r.ok

    # now we can allocate second order
    r = requests.post(
        f"{url}/allocate", json={"orderid": order2, "sku": sku, "qty": 100}
    )
    assert r.ok
    assert r.json()["batchref"] == batch
