from monstro.core.exceptions import MonstroError
from monstro.forms.exceptions import ValidationError


__all__ = (
    'ValidationError',
    'ORMError',
    'InvalidQuery'
)


class ORMError(MonstroError):

    pass


class InvalidQuery(ORMError):

    pass
