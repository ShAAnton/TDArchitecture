from flask import Flask, jsonify, request

from allocation import bootstrap
from allocation.domain import commands, exceptions
from allocation import views
from allocation.service_layer import unit_of_work, message_bus

import datetime

app = Flask(__name__)
mbus = bootstrap.bootstrap()


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
    mbus.handle(cmd)
    return 'OK', 201

@app.route("/deallocate", methods=['POST'])
def deallocate_endpoint():
    try:
        cmd = commands.Deallocate(
            order_id=request.json['order_id'],
            sku=request.json['sku'],
            quantity=request.json['quantity']
        )
        mbus.handle(cmd)
    except (exceptions.NotAllocatedLine, exceptions.InvalidSku) as e:
        return jsonify({'message': str(e)}), 400

    return 'OK', 201


@app.route("/allocate", methods=['POST'])
def allocate_endpoint():
    try:
        cmd = commands.Allocate(
            order_id=request.json['order_id'],
            sku=request.json['sku'],
            quantity=request.json['quantity']
        )
        mbus.handle(cmd)
    except exceptions.InvalidSku as e:
        return jsonify({'message': str(e)}), 400

    return "OK", 201


@app.route("/allocations/<order_id>", methods=["GET"])
def allocations_view_endpoint(order_id):
    result = views.allocations(order_id, mbus.uow)
    if not result:
        return "not found", 404
    return jsonify(result), 200

