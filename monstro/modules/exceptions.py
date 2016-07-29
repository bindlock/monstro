# coding=utf-8

from monstro.core.exceptions import MonstroError


class ModuleError(MonstroError):

    pass


class ModuleNotFound(ModuleError):

    pass
