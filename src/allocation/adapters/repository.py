import abc
from typing import Set
from allocation.domain import model
from allocation.adapters import orm
from allocation.adapters.orm import Session


class AbstractRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[model.Product] = set()

    def add(self, product: model.Product):
        self._add(product)
        self.seen.add(product)

    @abc.abstractmethod
    def _add(self, product: model.Product):
        raise NotImplementedError

    def get(self, sku) -> model.Product:
        product = self._get(sku)
        if product:
            self.seen.add(product)
        return product

    @abc.abstractmethod
    def _get(self, sku) -> model.Product:
        raise NotImplementedError

    def get_by_batch_ref(self, batch_ref: str):
        product = self._get_by_batch_ref(batch_ref)
        if product:
            self.seen.add(product)
        return product

    @abc.abstractmethod
    def _get_by_batch_ref(self, batch_ref: str):
        raise NotImplementedError



class SQLAlchemyRepository(AbstractRepository):

    def __init__(self, session: Session):
        super().__init__()
        self.session = session

    def _add(self, product):
        self.session.add(product)

    def _get(self, sku):
        return self.session.query(model.Product).filter_by(sku=sku).first()

    def _get_by_batch_ref(self, batch_ref):
        product = (self.session
                   .query(model.Product)
                   .join(model.Batch)
                   .filter(model.Batch.reference == batch_ref)
                   .first())
        return product