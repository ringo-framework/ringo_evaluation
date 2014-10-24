import sqlalchemy as sa
from ringo.model import Base
from ringo.model.base import BaseItem, BaseFactory
from ringo.model.mixins import Owned, Meta


class ExtensionFactory(BaseFactory):

    def create(self, user=None):
        new_item = BaseFactory.create(self, user)
        return new_item


class Extension(Owned, Meta, BaseItem, Base):
    """Docstring for evaluation extension"""

    __tablename__ = 'evaluations'
    """Name of the table in the database for this modul. Do not
    change!"""
    _modul_id = None
    """Will be set dynamically. See include me of this modul"""

    # Define columns of the table in the database
    id = sa.Column(sa.Integer, primary_key=True)
    modul_id = sa.Column('modul_id', sa.Integer, sa.ForeignKey("modules.id"))
    name = sa.Column('name', sa.Text)
    data = sa.Column('data', sa.LargeBinary)
    description = sa.Column('description', sa.Text)
    size = sa.Column('size', sa.Integer)
    mime = sa.Column('mime', sa.Text)

    # Define relations to other tables
    modul = sa.orm.relationship("ModulItem", backref="evaluations")

    @classmethod
    def get_item_factory(cls):
        return ExtensionFactory(cls)
