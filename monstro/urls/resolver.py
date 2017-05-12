import re

from tornado.util import import_object
from tornado.web import URLSpec


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
            matcher = url.matcher
            pattern = matcher.regex.pattern.lstrip('^').lstrip('/')

            matcher.regex = re.compile('{}/{}'.format(prefix, pattern))
            matcher._path, matcher._group_count = matcher._find_groups()

            if isinstance(resolver.namespace, str):
                url.name = '{}:{}'.format(resolver.namespace, url.name)

            yield url


def include(patterns, namespace=None):
    return Resolver(patterns, namespace)
