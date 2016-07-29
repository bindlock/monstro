# coding=utf-8

from tornado.web import url

from . import handlers


patterns = [
    url(r'^/$', handlers.IndexHandler, name='index')
]
