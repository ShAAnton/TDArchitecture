from flask import Flask, jsonify, request
from sqlalchemy import create_engine

from allocation import config
from allocation.domain import model
from allocation.adapters import orm, repository
from allocation.service_layer import services
from allocation.service_layer import unit_of_work

import datetime

orm.start_mappers()
app = Flask(__name__)

@app.route("/add_batch", methods=['POST'])
def add_batch():
    eta = request.json['eta']
    if eta is not None:
        eta = datetime.date.fromisoformat(eta)
    services.add_batch(
        batch_ref=request.json['batch_ref'],
        sku=request.json['sku'],
        quantity=request.json['quantity'],
        eta=eta,
        uow=unit_of_work.SqlAlchemyUnitOfWork()
    )
    return 'OK', 201

@app.route("/deallocate", methods=['POST'])
def deallocate():
    try:
        batch_ref = services.deallocate(
            order_id=request.json['order_id'],
            sku=request.json['sku'],
            quantity=request.json['quantity'],
            uow=unit_of_work.SqlAlchemyUnitOfWork()
        )
    except (model.NotAllocatedLine, services.InvalidSku) as e:
        return jsonify({'message': str(e)}), 400

    return jsonify({'batch_ref': batch_ref}), 201


@app.route("/allocate", methods=['POST'])
def allocate():
    try:
        batch_ref = services.allocate(
            order_id=request.json['order_id'],
            sku=request.json['sku'],
            quantity=request.json['quantity'],
            uow=unit_of_work.SqlAlchemyUnitOfWork()
        )
    except (model.OutOfStock, services.InvalidSku) as e:
        return jsonify({'message': str(e)}), 400

    return jsonify({'batch_ref': batch_ref}), 201


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}
