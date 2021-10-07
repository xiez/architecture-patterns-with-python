import abc

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import config
from adapters import repository


class AbstractUnitOfWork(abc.ABC):
    products: repository.AbstractProductRepository

    def __exit__(self, *args):
        self.rollback()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    @abc.abstractmethod
    def commit(self):
        ...

    @abc.abstractmethod
    def rollback():
        ...


DEFAULT_SESSION_FACTORY = sessionmaker(
    bind=create_engine(
        config.get_mysql_uri(),
        isolation_level="REPEATABLE READ",
    )
)


class SqlalchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory=DEFAULT_SESSION_FACTORY):
        self.session_factory = session_factory

    def __enter__(self):
        self.session = self.session_factory()  # type: Session
        self.products = repository.SqlAlchemyRepository(self.session)
        return super().__enter__()

    def __exit__(self, *args):
        super().__exit__(*args)
        self.session.close()

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()


class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.products = repository.FakeRepository([])
        self.committed = False

    def commit(self):
        self.committed = True

    def rollback(self):
        pass
