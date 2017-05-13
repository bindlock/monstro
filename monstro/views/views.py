import functools
import urllib.parse

import tornado.web

from monstro.forms import forms
from monstro.views import mixins


__all__ = (
    'View',
    'RedirectView',
    'TemplateView',
    'ListView',
    'DetailView',
    'FormView',
    'CreateView',
    'UpdateView',
    'DeleteView'
)


class View(tornado.web.RequestHandler):

    authenticators = ()

    @staticmethod
    def authenticated(argument=None):
        def decorator(method):
            @functools.wraps(method)
            async def wrapper(self, *args, **kwargs):
                for authenticator in await self.get_authenticators():
                    self.session = await authenticator.authenticate(self)

                    if self.session:
                        break
                else:
                    if callable(argument) or argument is None:
                        raise tornado.web.HTTPError(401)

                    redirect_url = argument

                    if isinstance(argument, str) and '?' not in argument:
                        if urllib.parse.urlparse(argument).scheme:
                            next_url = self.request.full_url()
                        else:
                            next_url = self.request.uri

                        redirect_url = '{}?{}'.format(
                            argument,
                            urllib.parse.urlencode(dict(next=next_url))
                        )

                    return self.redirect(redirect_url)

                return await method(self, *args, **kwargs)
            return wrapper
        return decorator(argument) if callable(argument) else decorator

    def initialize(self):
        self.session = None
        self.request.GET = {}
        self.request.POST = {}

    async def get_authenticators(self):
        return self.authenticators

    async def prepare(self):
        for key, value in self.request.query_arguments.items():
            self.request.GET[key] = value[0].decode('utf-8')

        for key, value in self.request.body_arguments.items():
            self.request.POST[key] = value[0].decode('utf-8')


class RedirectView(mixins.RedirectResponseMixin, tornado.web.RequestHandler):

    async def prepare(self):
        return self.redirect(await self.get_redirect_url(), self.permanent)


class TemplateView(View):

    template_name = None

    async def get_template_name(self):
        assert self.template_name, (
            'TemplateView requires either a definition of '
            '"template_name" or an implementation of "get_template_name()"'
        )

        return self.template_name

    async def get_context(self, **kwargs):
        return kwargs

    async def get(self, *args, **kwargs):
        self.render(
            await self.get_template_name(),
            **await self.get_context()
        )


class ListView(mixins.ListResponseMixin, TemplateView):

    context_object_name = 'pagination'

    async def get_context(self, **kwargs):
        context = {self.context_object_name: await self.paginate()}
        context.update(kwargs)
        return context


class DetailView(mixins.DetailResponseMixin, TemplateView):

    context_object_name = 'object'

    async def get_context(self, **kwargs):
        context = {self.context_object_name: await self.get_object()}
        context.update(kwargs)
        return context


class FormView(mixins.RedirectResponseMixin, TemplateView):

    form_class = None
    permanent = False

    async def get_form_class(self):
        assert self.form_class, (
            'FormView requires either a definition of '
            '"form_class" or an implementation of "get_form_class()"'
        )

        return self.form_class

    async def get_form_kwargs(self):
        return {'data': self.request.POST}

    async def get_form(self):
        return (await self.get_form_class())(**await self.get_form_kwargs())  # pylint:disable=E1102

    async def get_context(self, **kwargs):
        context = await super().get_context()
        context.update(kwargs)
        context.setdefault('form', await self.get_form())

        return context

    async def post(self, *args, **kwargs):
        form = await self.get_form()

        if await form.is_valid():
            return await self.form_valid(form)

        return await self.form_invalid(form)

    async def form_valid(self, form):  # pylint: disable=W0613
        return self.redirect(await self.get_redirect_url(), self.permanent)

    async def form_invalid(self, form):
        context = await self.get_context(form=form)
        self.render(self.template_name, **context)


class CreateView(mixins.ModelResponseMixin, FormView):

    async def get_form_class(self):
        if self.form_class:  # pragma: no cover
            return self.form_class

        Meta = type('Meta', (), {'model': await self.get_model()})
        return type('ModelForm', (forms.ModelForm,), {'Meta': Meta})

    async def form_valid(self, form):
        await form.save()
        return await super().form_valid(form)


class UpdateView(mixins.DetailResponseMixin, CreateView):  # pylint:disable=R0901

    async def get_form_kwargs(self):
        kwargs = await super().get_form_kwargs()
        kwargs['instance'] = await self.get_object()
        return kwargs


class DeleteView(mixins.RedirectResponseMixin,
                 mixins.DetailResponseMixin,
                 View):

    async def delete(self, *args, **kwargs):
        await (await self.get_object()).delete()
        return self.redirect(await self.get_redirect_url(), self.permanent)
