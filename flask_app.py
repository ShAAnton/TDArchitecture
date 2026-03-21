from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
import model
import orm
import repository

orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask(__name__)

@app.route("/allocate", methods=['POST'])
def allocate_endpoint():
    session = get_session()
    batches = repository.SQLAlchemyRepository(session).list()
    line = model.OrderLine(
        order_id=request.json['order_id'],
        sku=request.json['sku'],
        quantity=request.json['quantity']
    )
    if not is_valid_sku(line.sku, batches):
        return jsonify({'message': f'Invalid sku {line.sku}'}), 400
    try:
        batch_ref = model.allocate(line, batches)
    except model.OutOfStock as e:
        return jsonify({'message': str(e)}), 400

    session.commit()
    return jsonify({'batch_ref': batch_ref}), 201


def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}
