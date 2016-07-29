# Monstro #
*Web framework based on Tornado and MongoDB*

[![PyPI](http://img.shields.io/pypi/v/monstro.svg?style=flat)](https://pypi.python.org/pypi/monstro)
[![Documentation Status](http://readthedocs.org/projects/monstro/badge/?version=latest)](http://monstro.readthedocs.org/en/latest/?badge=latest)

## Installation ##

`pip install monstro`

## Getting started ##

### Create new project ###
```
monstro new project example
cd example
```

### Create new module ###
```
monstro new module modules/example
```

### Update settings ###
Set `secret_key` and add `example` to `modules` in `settings/base`.

### Run server ###
```
./manage.py run
```

## Documentation ##
[Read the Docs](http://monstro.readthedocs.org/)

## Tests ##
```bash
tox
```

## Changelog ##
See [releases](https://github.com/pyvim/monstro/releases)

## License ##
See [LICENSE](https://github.com/pyvim/monstro/blob/master/LICENSE)
