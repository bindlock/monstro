# coding=utf-8

import tornado.web
import tornado.util

from monstro.conf import settings


application = tornado.web.Application(
    tornado.util.import_object(settings.urls),
    cookie_secret=settings.secret_key,
    debug=settings.debug,
    **getattr(settings, 'tornado_application_settings', {})
)
