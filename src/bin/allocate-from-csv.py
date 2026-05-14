import csv
import sys
from pathlib import Path
from allocation.service_layer.unit_of_work import CSVUnitOfWork
from allocation.service_layer import services

def main(folder):
    orders_path = Path(folder) / 'orders.csv'
    csv_uow = CSVUnitOfWork(folder)
    with orders_path.open() as orders_file:
        reader = csv.DictReader(orders_file)
        for row in reader:
            order_id, sku = row['order_id'], row['sku']
            quantity = int(row['quantity'])
            services.allocate(order_id, sku, quantity, csv_uow)


if __name__ == '__main__':
    main(sys.argv[1])
