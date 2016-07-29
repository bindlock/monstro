# coding=utf-8

from monstro import orm


class Model(orm.Model):

    __collection__ = 'models'

    name = orm.StringField(unique=True)

    def __str__(self):
        return self.name
