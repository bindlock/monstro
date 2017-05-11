from tornado.util import import_object
import tornado.ioloop

from monstro.conf import settings
from monstro.core.exceptions import ImproperlyConfigured
from monstro.db.migrations.models import Migration
from monstro.management import Command


class ApplyMigrations(Command):

    def execute(self, arguments):
        try:
            migrations = settings.migrations or []
        except AttributeError:
            raise ImproperlyConfigured(
                'You must either define the settings variable "migrations".'
            )

        tornado.ioloop.IOLoop.instance().run_sync(
            lambda: self._migrate(migrations)
        )


    async def _migrate(self, migrations):
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
