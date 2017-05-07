import collections


class Choices(object):

    """Choice model.

    choices = Choice(
        ('NAME1', 'value1' 'Description NAME1'),
        ('NAME2', 'value2', 'Description NAME2'),
    )
    choices.NAME1
    >>> value1
    choices.choices
    >>> (('value1', 'Description NAME1'), ('value2', 'Description NAME2'))
    """

    __keys = ('name', 'value', 'description')

    def __init__(self, *args):
        self.__data = collections.OrderedDict()

        for item in args:
            item = dict(zip(self.__keys, item))
            self.__data[item['name']] = (item['value'], item['description'])

    def __getattr__(self, name):
        try:
            return self.__data[name][0]
        except KeyError:
            raise AttributeError(name)

    def __contains__(self, key):
        return key in self.values

    @property
    def choices(self):
        return self.__data.values()

    @property
    def values(self):
        return [choice[0] for choice in self.choices]
