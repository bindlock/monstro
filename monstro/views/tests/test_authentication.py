# coding=utf-8

import monstro.testing
from monstro.forms import String
from monstro.orm import Model

from monstro.views.authentication import (
    Authentication, HeaderAuthentication, CookieAuthentication
)

class User(Model):

    __collection__ = 'users'

    value = String()


class AuthenticationTest(monstro.testing.AsyncTestCase):

    async def test_get_credentials__not_implemented(self):
        with self.assertRaises(NotImplementedError):
            await Authentication().get_credentials(None)

    async def test_authenticate__not_implemented(self):
        with self.assertRaises(NotImplementedError):
            await Authentication().authenticate(None)


class CookieAuthenticationTest(monstro.testing.AsyncTestCase):

    class User(Model):

        __collection__ = 'tokens'

        value = String()

    authentication = CookieAuthentication(User, 'value')

    async def test_authenticate(self):
        user = await self.User.objects.create(value='cookie')
        view = type(
            'View', (object,),
            {'get_secure_cookie': lambda *args, **kwargs: user.value}
        )

        auth = await self.authentication.authenticate(view)

        self.assertEqual(user._id, auth._id)

    async def test_authenticate__error(self):
        view = type(
            'View', (object,),
            {'get_secure_cookie': lambda *args, **kwargs: 'wrong'}
        )

        auth = await self.authentication.authenticate(view)

        self.assertEqual(None, auth)


class HeaderAuthenticationTest(monstro.testing.AsyncTestCase):

    class Token(Model):

        __collection__ = 'tokens'

        value = String()

    authentication = HeaderAuthentication(Token, 'value')

    async def test_authenticate(self):
        token = await self.Token.objects.create(value='token')
        request = type(
            'Request', (object,), {'headers': {'Authorization': token.value}}
        )
        view = type('View', (object,), {'request': request})

        auth = await self.authentication.authenticate(view)

        self.assertEqual(token._id, auth._id)

    async def test_authenticate__error(self):
        request = type(
            'Request', (object,), {'headers': {'Authorization': 'wrong'}}
        )
        view = type('View', (object,), {'request': request})

        auth = await self.authentication.authenticate(view)

        self.assertEqual(None, auth)
