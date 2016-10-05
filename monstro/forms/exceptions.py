# coding=utf-8

from monstro.core.exceptions import MonstroError


class FormError(MonstroError):

    pass


class ValidationError(FormError):

    def __init__(self, error=None, field=None):
        self.error = error
        self.field = field

        super().__init__(self.__str__())

    def __str__(self):
        if self.field:
            return '{} - {}'.format(self.field, self.error)

        return str(self.error)
