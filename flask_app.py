from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
import model
import orm
import repository
import services

import datetime

orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask(__name__)

@app.route("/add_batch", methods=['POST'])
def add_batch():
    session = get_session()
    repo = repository.SQLAlchemyRepository(session)
    eta = request.json['eta']
    if eta is not None:
        eta = datetime.date.fromisoformat(eta)
    services.add_batch(
        batch_ref=request.json['batch_ref'],
        sku=request.json['sku'],
        quantity=request.json['quantity'],
        eta=eta,
        repo=repo,
        session=session
    )
    return 'OK', 201

@app.route("/deallocate", methods=['POST'])
def deallocate():
    session = get_session()
    repo = repository.SQLAlchemyRepository(session)
    try:
        batch_ref = services.deallocate(
            order_id=request.json['order_id'],
            sku=request.json['sku'],
            quantity=request.json['quantity'],
            repo=repo,
            session=session
        )
    except (model.NotAllocatedLine, services.InvalidSku) as e:
        return jsonify({'message': str(e)}), 400

    return jsonify({'batch_ref': batch_ref}), 201


@app.route("/allocate", methods=['POST'])
def allocate():
    session = get_session()
    repo = repository.SQLAlchemyRepository(session)
    try:
        batch_ref = services.allocate(
            order_id=request.json['order_id'],
            sku=request.json['sku'],
            quantity=request.json['quantity'],
            repo=repo,
            session=session
        )
    except (model.OutOfStock, services.InvalidSku) as e:
        return jsonify({'message': str(e)}), 400

    return jsonify({'batch_ref': batch_ref}), 201


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}
