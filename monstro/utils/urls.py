# coding=utf-8

import re

from tornado.util import import_object


def include(prefix, urls, namespace=None):
    if isinstance(urls, str):
        urls = import_object(urls)

    for url in urls:
        pattern = '{}{}'.format(prefix, url.regex.pattern).replace('//', '/')
        url.regex = re.compile(pattern)

        if namespace and url.name:
            url.name = '{}:{}'.format(namespace, url.name)

    return urls
