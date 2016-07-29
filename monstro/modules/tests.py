# coding=utf-8

import unittest

from monstro.core.exceptions import MonstroError
from monstro.modules import ModuleConfiguration, ModulesRegistry
from monstro.orm.model import Model

from .exceptions import ModuleNotFound


class ModuleConfigurationTest(unittest.TestCase):

    def test_init(self):
        instance = ModuleConfiguration('monstro.core')

        self.assertEqual('monstro.core', instance.module_path)
        self.assertEqual('core', instance.name)
        self.assertEqual('Core', instance.verbose_name)
        self.assertEqual('monstro.core.urls.patterns', instance.urls_path)
        self.assertEqual('monstro.core.models', instance.models_path)
        self.assertEqual(None, instance.models)
        self.assertEqual(None, instance.urls)

    def test_new(self):
        instance = type(
            'ModuleConfiguration', (ModuleConfiguration,),
            {
                'name': 'name',
                'verbose_name': 'Verbose Name',
                'urls_path': 'patterns.list',
                'models_path': 'models_list'
            }
        )('monstro.core')

        self.assertEqual('monstro.core', instance.module_path)
        self.assertEqual('name', instance.name)
        self.assertEqual('Verbose Name', instance.verbose_name)
        self.assertEqual('monstro.core.patterns.list', instance.urls_path)
        self.assertEqual('monstro.core.models_list', instance.models_path)
        self.assertEqual(None, instance.models)
        self.assertEqual(None, instance.urls)

    def test_get_urls(self):
        instance = type(
            'ModuleConfiguration', (ModuleConfiguration,),
            {'urls_path': 'exceptions.MonstroError'}
        )('monstro.core')

        self.assertEqual(MonstroError, instance.get_urls())
        self.assertEqual(MonstroError, instance.urls)

    def test_get_urls__not_exists(self):
        instance = ModuleConfiguration('monstro.core')

        self.assertEqual([], instance.get_urls())

    def test_get_models(self):
        instance = type(
            'ModuleConfiguration', (ModuleConfiguration,),
            {'models_path': 'model'}
        )('monstro.orm')

        self.assertEqual([Model], instance.get_models())
        self.assertEqual([Model], instance.models)

    def test_get_models__not_exists(self):
        instance = ModuleConfiguration('monstro.core')

        self.assertEqual([], instance.get_models())


class ModulesRegistryTest(unittest.TestCase):

    def test_init(self):
        instance = ModulesRegistry(['monstro.core'])

        self.assertEqual(['monstro.core'], instance.paths)
        self.assertEqual({'monstro.core': None}, instance.modules)

    def test_get(self):
        instance = ModulesRegistry(['monstro.core'])

        configuration = instance.get('monstro.core')

        self.assertIsInstance(configuration, ModuleConfiguration)
        self.assertEqual('core', configuration.name)

    def test_get__not_exists(self):
        instance = ModulesRegistry(['monstro.core'])

        with self.assertRaises(ModuleNotFound):
            instance.get('core')

    def test_get__custom_configuration(self):
        import monstro.core
        monstro.core.Configuration = type(
            'ModuleConfiguration', (ModuleConfiguration,), {'name': 'name'}
        )
        instance = ModulesRegistry(['monstro.core'])

        configuration = instance.get('monstro.core')

        self.assertIsInstance(configuration, ModuleConfiguration)
        self.assertEqual('name', configuration.name)

    def test_get_urls(self):
        import monstro.core
        monstro.core.Configuration = type(
            'ModuleConfiguration', (ModuleConfiguration,),
            {'urls_path': 'urls'}
        )
        monstro.core.urls = ['test']
        instance = ModulesRegistry(['monstro.core'])

        self.assertEqual(['test'], instance.get_urls())
