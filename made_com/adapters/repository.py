import abc

from domain import models


class AbstractProductRepository(abc.ABC):
    @abc.abstractmethod
    def add(self, product: models.Product):
        ...

    @abc.abstractmethod
    def get(self, sku: str) -> models.Product:
        ...


class SqlAlchemyRepository(AbstractProductRepository):
    def __init__(self, session):
        self.session = session

    def add(self, product):
        self.session.add(product)

    def get(self, sku):
        return (
            self.session.query(models.Product).filter_by(sku=sku)
            # .with_for_update()
            .first()
        )

    def list(self):
        return self.session.query(models.Product).all()


class FakeRepository(AbstractProductRepository):
    def __init__(self, products):
        self._products = set(products)

    def add(self, product):
        self._products.add(product)

    def get(self, sku):
        return next((p for p in self._products if p.sku == sku), None)

    def list(self):
        return list(self._products)
