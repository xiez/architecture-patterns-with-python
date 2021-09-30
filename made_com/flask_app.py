from flask import Flask, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
import models
import orm
import repository

orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask(__name__)


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}


@app.route("/", methods=["GET"])
def home():
    return "ok", 200


@app.route("/allocate", methods=["POST"])
def allocate_endpoint():
    session = get_session()
    batches = repository.SqlAlchemyRepository(session).list()

    req_j = request.json
    line = models.OrderLine(req_j["orderid"], req_j["sku"], req_j["qty"])

    if not is_valid_sku(line.sku, batches):
        return {"message": f"Invalid sku {line.sku}"}, 400

    try:
        batchref = models.allocate(line, batches)
    except models.OutOfStock as e:
        return {"message": str(e)}, 400

    session.commit()
    return {"batchref": batchref}, 201
