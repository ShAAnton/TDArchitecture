import csv
import sys
from pathlib import Path
from datetime import datetime
from allocation.domain import model


def load_batches(batches_path):
    batches = []
    with batches_path.open() as batches_file:
        reader = csv.DictReader(batches_file)
        for row in reader:
            if row['eta']:
                eta = datetime.strptime(row['eta'], '%Y-%m-%d').date()
            else:
                eta = None
            batches.append(model.Batch(
                ref = row['batch_ref'],
                sku = row['sku'],
                quantity = int(row['quantity']),
                eta = eta
            ))
    return batches


def main(folder):
    batches_path = Path(folder) / 'batches.csv'
    orders_path = Path(folder) / 'orders.csv'
    allocations_path = Path(folder) / 'allocations.csv'

    batches = load_batches(batches_path)

    with (orders_path.open() as orders_file,
          allocations_path.open('w') as allocations_file):
        reader = csv.DictReader(orders_file)
        writer = csv.writer(allocations_file, lineterminator='\n')
        writer.writerow(['order_id', 'sku', 'batch_ref'])
        for row in reader:
            order_id, sku = row['order_id'], row['sku']
            quantity = int(row['quantity'])
            line = model.OrderLine(order_id, sku, quantity)
            batch_ref = model.allocate(line, batches)
            writer.writerow([line.order_id, line.sku, batch_ref])

if __name__ == '__main__':
    main(sys.argv[1])
