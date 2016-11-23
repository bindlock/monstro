import tornado.ioloop
from tornado.util import import_object

from monstro.conf import settings
from monstro.core.exceptions import ImproperlyConfigured
from monstro.orm.migrations.models import Migration


def execute(args):
    try:
        migrations = settings.migrations or []
    except AttributeError:
        raise ImproperlyConfigured(
            'You must either define the settings variable "migrations".'
        )

    tornado.ioloop.IOLoop.instance().run_sync(lambda: _migrate(migrations))


async def _migrate(migrations):
    for path in migrations:
        try:
            migration = import_object(path)
        except ImportError:
            raise ImproperlyConfigured(
                'Cannot import migration "{}".'.format(migration)
            )

        if not await Migration.objects.filter(name=path).count():
            await migration().execute()
            await Migration.objects.create(name=path)

        print('{} applied.'.format(path))
