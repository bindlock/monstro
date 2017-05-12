from monstro.db import Model, String
import monstro.testing

from monstro.views.authenticators import (
    Authenticator, HeaderAuthenticator, CookieAuthenticator
)

class User(Model):

    value = String()

    class Meta:
        collection = 'users'


class AuthenticatorTest(monstro.testing.AsyncTestCase):

    async def test_get_credentials__not_implemented(self):
        with self.assertRaises(NotImplementedError):
            await Authenticator().get_credentials(None)

    async def test_authenticate__not_implemented(self):
        with self.assertRaises(NotImplementedError):
            await Authenticator().authenticate(None)


class CookieAuthenticatorTest(monstro.testing.AsyncTestCase):

    class User(Model):

        value = String()

        class Meta:
            collection = 'tokens'

    authenticator = CookieAuthenticator(User, 'value')

    async def test_authenticate(self):
        user = await self.User.objects.create(value='cookie')
        view = type(
            'View', (object,),
            {'get_secure_cookie': lambda *args, **kwargs: user.value.encode()}
        )

        auth = await self.authenticator.authenticate(view)

        self.assertEqual(user._id, auth._id)

    async def test_authenticate__error(self):
        view = type(
            'View', (object,),
            {'get_secure_cookie': lambda *args, **kwargs: b'wrong'}
        )

        auth = await self.authenticator.authenticate(view)

        self.assertEqual(None, auth)


class HeaderAuthenticatorTest(monstro.testing.AsyncTestCase):

    class Token(Model):

        value = String()

        class Meta:
            collection = 'tokens'

    authenticator = HeaderAuthenticator(Token, 'value')

    async def test_authenticate(self):
        token = await self.Token.objects.create(value='token')
        request = type(
            'Request', (object,), {'headers': {'Authorization': token.value}}
        )
        view = type('View', (object,), {'request': request})

        auth = await self.authenticator.authenticate(view)

        self.assertEqual(token._id, auth._id)

    async def test_authenticate__error(self):
        request = type(
            'Request', (object,), {'headers': {'Authorization': 'wrong'}}
        )
        view = type('View', (object,), {'request': request})

        auth = await self.authenticator.authenticate(view)

        self.assertEqual(None, auth)
