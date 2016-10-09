# coding=utf-8

from tornado.web import url


__all__ = ('url', 'Resolver')


class Resolver(object):

    def __init__(self, patterns):
        self.patterns = patterns

    def resolve(self):
        urls = []

        for pattern in self.patterns:
            if isinstance(pattern, dict):
                urls.append(url(**pattern))
            else:
                urls.append(url(*pattern))

        return urls
