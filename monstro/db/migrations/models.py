from monstro import db


class Migration(db.Model):

    name = db.String(unique=True)

    class Meta:
        collection = '__migrations__'
