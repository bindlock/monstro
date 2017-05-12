class Settings(object):

    secret_key = 'default'
    debug = True

    databases = [
        {
            'uri': 'mongodb://localhost:27017',
            'name': 'test',
        }
    ]

    urls = 'random'
