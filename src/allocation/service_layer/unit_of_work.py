import abc
import allocation.adapters.repository as repository

from allocation import config
from allocation.adapters.orm import sessionmaker, Session, create_engine

class AbstractionUnitOfWork(abc.ABC):
    batches: repository.AbstractRepository

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.rollback()

    @abc.abstractmethod
    def commit(self):
        raise NotImplementedError

    @abc.abstractmethod
    def rollback(self):
        raise NotImplementedError


DEFALUT_ENGINE = create_engine(config.get_postgres_uri())
DEFAULT_SESSION_FACTORY = sessionmaker(bind=DEFALUT_ENGINE)


class SqlAlchemyUnitOfWork(AbstractionUnitOfWork):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory

    def __enter__(self, *args):
        self.session: Session = self.session_factory()
        self.batches = repository.SQLAlchemyRepository(self.session)
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()
