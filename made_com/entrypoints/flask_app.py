from flask import Flask, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
from domain import models
from adapters import orm, repository
from service_layer import services

orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask(__name__)


@app.route("/", methods=["GET"])
def home():
    return "ok", 200


@app.route("/batches", methods=["POST"])
def add_batches_endpoint():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    req_j = request.json
    batch = models.Batch(req_j["reference"], req_j["sku"], req_j["qty"], req_j["eta"])

    services.add_batch(batch, repo, session)
    return {"batchref": batch.reference}, 201


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    req_j = request.json
    line = models.OrderLine(req_j["orderid"], req_j["sku"], req_j["qty"])

    try:
        batchref = services.allocate(line, repo, session)
    except (models.OutOfStock, services.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 201


@app.route("/deallocate", methods=["POST"])
def deallocate_endpoint():
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    req_j = request.json
    line = models.OrderLine(req_j["orderid"], req_j["sku"], -1)

    try:
        batchref = services.deallocate(line, repo, session)
    except (models.OrderLineNotFound, services.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 200
