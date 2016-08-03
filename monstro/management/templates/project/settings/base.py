# coding=utf-8


class Settings(object):

    secret_key = ''
    debug = False
    mongodb_uri = 'mongodb://localhost:27017'
    mongodb_database = 'test'
    modules = []

    tornado_settings = {
        'template_path': '',
        'static_path': '',
    }
    test_settings = [
        'modules',
    ]
