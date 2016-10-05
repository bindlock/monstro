# coding=utf-8

from monstro.core.exceptions import MonstroError


class ORMError(MonstroError):

    pass


class DoesNotExist(ORMError):

    pass


class InvalidQuery(ORMError):

    pass
