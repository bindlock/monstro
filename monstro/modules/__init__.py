# coding=utf-8

from tornado.util import import_object

from .exceptions import ModuleNotFound


class ModuleConfiguration(object):

    name = None
    verbose_name = None
    urls_path = 'urls.patterns'
    models_path = 'models'

    def __init__(self, module_path):
        self.module_path = module_path
        self.name = self.name or module_path.split('.')[-1]
        self.verbose_name = self.verbose_name or self.name.title()

        self.urls_path = '{0.module_path}.{0.urls_path}'.format(self)
        self.models_path = '{0.module_path}.{0.models_path}'.format(self)

        self.models = None
        self.urls = None

    def get_urls(self):
        if self.urls is None:
            try:
                self.urls = import_object(self.urls_path)
            except ImportError:
                self.urls = []

        return self.urls

    def get_models(self):
        if self.models is None:
            self.models = []

            try:
                module = import_object(self.models_path)
            except ImportError:
                return self.models

            for value in module.__dict__.values():
                if hasattr(value, '__collection__'):
                    self.models.append(value)

        return self.models


class ModulesRegistry(object):

    def __init__(self, paths):
        self.paths = paths

        self.modules = {path: None for path in self.paths}

    def get(self, path):
        configuration = self.modules.get(path)

        if configuration is None:
            try:
                module = import_object(path)
            except ImportError:
                raise ModuleNotFound(path)

            if hasattr(module, 'Configuration'):
                configuration = self.set(path, module.Configuration)
            else:
                configuration = self.set(path)

        return configuration

    def set(self, path, configuration_class=ModuleConfiguration):
        self.modules[path] = configuration_class(path)
        return self.modules[path]

    def get_urls(self):
        urls = []

        for path in self.modules.keys():
            urls.extend(self.get(path).get_urls())

        return urls
