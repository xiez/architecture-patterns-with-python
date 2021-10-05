from datetime import datetime

from flask import Flask, request

from domain import models
from adapters import orm
from service_layer import services, unit_of_work

app = Flask(__name__)
orm.start_mappers()


@app.route("/", methods=["GET"])
def home():
    return "ok", 200


@app.route("/batches", methods=["POST"])
def add_batches_endpoint():
    uow = unit_of_work.SqlalchemyUnitOfWork()
    req_j = request.json
    if req_j["eta"] is not None:
        eta = datetime.fromisoformat(req_j["eta"]).date()
    else:
        eta = None
    services.add_batch(req_j["reference"], req_j["sku"], req_j["qty"], eta, uow)
    return {"batchref": req_j["reference"]}, 201


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    uow = unit_of_work.SqlalchemyUnitOfWork()
    req_j = request.json

    try:
        batchref = services.allocate(req_j["orderid"], req_j["sku"], req_j["qty"], uow)
    except (models.OutOfStock, services.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 201


@app.route("/deallocate", methods=["POST"])
def deallocate_endpoint():
    uow = unit_of_work.SqlalchemyUnitOfWork()
    req_j = request.json

    try:
        batchref = services.deallocate(req_j["orderid"], req_j["sku"], -1, uow)
    except (models.OrderLineNotFound, services.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 200
