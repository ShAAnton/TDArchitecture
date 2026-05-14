import abc
from allocation.domain import model
from allocation.adapters.orm import Session
from allocation.domain.model import OrderLine


class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch: model.Batch):
        raise NotImplementedError

    @abc.abstractmethod
    def get(self, reference) -> model.Batch:
        raise NotImplementedError

    @abc.abstractmethod
    def list(self):
        raise NotImplementedError


class SQLAlchemyRepository(AbstractRepository):
    def __init__(self, session: Session):
        self.session = session

    def add(self, batch):
        self.session.add(batch)

    def get(self, reference):
        return self.session.query(model.Batch).filter_by(reference=reference).one()

    def list(self):
        return self.session.query(model.Batch).all()


from pathlib import Path
import csv
from datetime import datetime


class CSVRepository(AbstractRepository):
    def __init__(self, folder):
        self._batches_path = Path(folder) / "batches.csv"
        self._allocations_path = Path(folder) / "allocations.csv"
        self._batches = {} # type: Dict[str, model.Batch]
        self._load()

    def _load(self):
        with self._batches_path.open() as batches_file:
            reader = csv.DictReader(batches_file)
            for row in reader:
                ref = row['batch_ref']
                sku = row['sku']
                if row['eta']:
                    eta = datetime.strptime(row['eta'], '%Y-%m-%d').date()
                else:
                    eta = None
                self._batches[ref] = model.Batch(
                    ref=ref,
                    sku=sku,
                    quantity=int(row['quantity']),
                    eta=eta
                )
        if self._allocations_path.exists() is False:
            return
        with self._allocations_path.open() as f_all:
            reader = csv.DictReader(f_all)
            for row in reader:
                batch_ref, order_id, sku = row["batch_ref"], row["order_id"], row["sku"]
                quantity = int(row["quantity"])
                line = OrderLine(order_id, sku, quantity)
                batch = self._batches[batch_ref]
                batch._allocations.add(line)

    def add(self, batch: model.Batch):
        self._batches[batch.reference] = batch

    def get(self, reference) -> model.Batch:
        return self._batches.get(reference)

    def list(self):
        return list(self._batches.values())