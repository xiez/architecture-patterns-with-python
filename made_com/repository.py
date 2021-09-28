import abc

import models

class AbstractRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, batch):
        ...

    @abc.abstractmethod
    def get(self, reference):
        ...


class SqlAlchemyRepository(AbstractRepository):
    def __init__(self, session):
        self.session = session

    def add(self, batch):
        self.session.add(batch)

    def get(self, reference):
        return self.session.query(models.Batch).filter_by(reference=reference).one()

    def list(self):
        return self.session.query(models.Batch).all()
