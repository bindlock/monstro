# coding=utf-8

import re

from tornado.web import URLSpec
from tornado.util import import_object


class Resolver(object):

    def __init__(self, patterns, namespace=None):
        self.patterns = patterns
        self.namespace = namespace

    def __iter__(self):
        return self.resolve()

    def resolve(self):
        if isinstance(self.patterns, str):
            self.patterns = import_object(self.patterns)

        for pattern in self.patterns:
            if isinstance(pattern, dict):
                yield URLSpec(**pattern)
            elif isinstance(pattern, URLSpec):
                yield pattern
            elif isinstance(pattern, Resolver):
                yield from pattern.resolve()
            elif len(pattern) > 1 and isinstance(pattern[1], Resolver):
                yield from self.include(*pattern)
            else:
                yield URLSpec(*pattern)

    def include(self, prefix, resolver):
        prefix = prefix.rstrip('$').rstrip('/')

        for url in resolver.resolve():
            pattern = url.regex.pattern.lstrip('^').lstrip('/')

            url.regex = re.compile('{}/{}'.format(prefix, pattern))
            url._path, url._group_count = url._find_groups()

            if isinstance(resolver.namespace, str):
                url.name = '{}:{}'.format(resolver.namespace, url.name)

            yield url


def include(patterns, namespace=None):
    return Resolver(patterns, namespace)
