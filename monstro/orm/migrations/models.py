from monstro import orm


class Migration(orm.Model):

    __collection__ = '__migrations__'

    name = orm.String(unique=True)
