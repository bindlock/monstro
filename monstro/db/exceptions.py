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

    def __init__(self, message, model, field, query=None):
        super().__init__(message)

        self.model = model
        self.field = field
        self.query = query or {}
