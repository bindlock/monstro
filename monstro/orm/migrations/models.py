from monstro import orm


class Migration(orm.Model):

    name = orm.String(unique=True)

    class Meta:
        collection = '__migrations__'
