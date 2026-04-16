from flask import Flask, jsonify, request
from sqlalchemy import create_engine

from allocation import config
from allocation.domain import events, commands, exceptions
from allocation.adapters import orm, repository
# from allocation.service_layer import handlers
from allocation.service_layer import unit_of_work, message_bus

import datetime

orm.start_mappers()
app = Flask(__name__)

@app.route("/add_batch", methods=['POST'])
def add_batch():
    eta = request.json['eta']
    if eta is not None:
        eta = datetime.date.fromisoformat(eta)
    cmd = commands.CreateBatch(
        reference=request.json['batch_ref'],
        sku=request.json['sku'],
        quantity=request.json['quantity'],
        eta=eta
    )
    uow = unit_of_work.SqlAlchemyUnitOfWork()
    message_bus.MessageBus(uow).handle(cmd)
    return 'OK', 201

@app.route("/deallocate", methods=['POST'])
def deallocate():
    try:
        cmd = commands.Deallocate(
            order_id=request.json['order_id'],
            sku=request.json['sku'],
            quantity=request.json['quantity']
        )
        uow = unit_of_work.SqlAlchemyUnitOfWork()
        batch_ref = message_bus.MessageBus(uow).handle(cmd).pop(0)
    except (exceptions.NotAllocatedLine, exceptions.InvalidSku) as e:
        return jsonify({'message': str(e)}), 400

    return jsonify({'batch_ref': batch_ref}), 201


@app.route("/allocate", methods=['POST'])
def allocate():
    try:
        cmd = commands.Allocate(
            order_id=request.json['order_id'],
            sku=request.json['sku'],
            quantity=request.json['quantity']
        )
        uow = unit_of_work.SqlAlchemyUnitOfWork()
        batch_ref = message_bus.MessageBus(uow).handle(cmd).pop(0)

        if batch_ref is None:
            return jsonify({'message': f"Fail to allocate order {request.json['order_id']}"}), 400
    except exceptions.InvalidSku as e:
        return jsonify({'message': str(e)}), 400

    return jsonify({'batch_ref': batch_ref}), 201


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}
