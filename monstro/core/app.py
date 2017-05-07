import tornado.web
import tornado.util

from monstro.conf import settings
from monstro.urls import urls


application = tornado.web.Application(
    urls(settings.urls),
    cookie_secret=settings.secret_key,
    debug=settings.debug,
    **getattr(settings, 'tornado_application_settings', {})
)
