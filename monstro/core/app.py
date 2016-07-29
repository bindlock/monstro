# coding=utf-8

import tornado.web

from monstro.conf import settings, modules


application = tornado.web.Application(
    modules.get_urls(),
    cookie_secret=settings.secret_key,
    debug=settings.debug,
    **getattr(settings, 'tornado_settings', {})
)
