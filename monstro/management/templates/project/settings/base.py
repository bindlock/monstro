# coding=utf-8

import os


class Settings(object):

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    secret_key = ''
    debug = False
    mongodb_uri = 'mongodb://localhost:27017/test'
    mongodb_client_settings = {}

    urls = 'urls.patterns'

    tornado_application_settings = {
        'static_path': os.path.join(base_dir, 'static/'),
        'template_path': os.path.join(base_dir, 'templates/'),
    }

    nosetests_arguments = [
        'modules',
    ]
