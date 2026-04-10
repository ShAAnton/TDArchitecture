import abc
import allocation.adapters.repository as repository

from allocation import config
from allocation.adapters.orm import sessionmaker, Session, create_engine
import allocation.service_layer.message_bus as message_bus

class AbstractionUnitOfWork(abc.ABC):
    products: repository.AbstractRepository

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.rollback()

    def commit(self):
        self._commit()
        self.publish_events()

    @abc.abstractmethod
    def _commit(self):
        raise NotImplementedError

    def publish_events(self):
        for product in self.products.seen:
            while product.events:
                event = product.events.pop(0)
                message_bus.handle(event)

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError



DEFAULT_ENGINE = create_engine(
    config.get_postgres_uri(),
    isolation_level='REPEATABLE READ'
)
DEFAULT_SESSION_FACTORY = sessionmaker(bind=DEFAULT_ENGINE)


class SqlAlchemyUnitOfWork(AbstractionUnitOfWork):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory

    def __enter__(self, *args):
        self.session: Session = self.session_factory()
        self.products = repository.SQLAlchemyRepository(self.session)
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def _commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
