# coding=utf-8

import tornado.web

from . import mixins


class View(tornado.web.RequestHandler):

    authentication = None

    def initialize(self):
        self.request.GET = {}
        self.request.POST = {}

        self.authentication = self.get_authentication()

    def get_authentication(self):
        return self.authentication

    async def prepare(self):
        if self.authentication:
            self.current_user = await self.authentication.authenticate(self)

            if not self.current_user:
                return self.send_error(401, reason='Authentication failed')

        for key, value in self.request.query_arguments.items():
            self.request.GET[key] = value[0].decode('utf-8')

        for key, value in self.request.body_arguments.items():
            self.request.POST[key] = value[0].decode('utf-8')


class RedirectView(mixins.RedirectResponseMixin, tornado.web.RequestHandler):

    def prepare(self):
        return self.redirect(self.get_redirect_url(), self.permanent)


class TemplateView(View):

    template_name = None

    def initialize(self):
        super().initialize()
        self.template_name = self.get_template_name()

        assert self.template_name, (
            'TemplateView requires either a definition of '
            '"template_name" or an implementation of "get_template_name()"'
        )

    def get_template_name(self):
        return self.template_name

    async def get_context_data(self):
        return {}

    async def get(self, *args, **kwargs):
        self.render(self.template_name, **await self.get_context_data())


class ListView(mixins.ListResponseMixin, TemplateView):

    context_object_name = 'objects'

    async def get_context_data(self):
        return {self.context_object_name: await self.paginate()}


class DetailView(mixins.DetailResponseMixin, TemplateView):

    context_object_name = 'object'

    async def get_context_data(self):
        return {self.context_object_name: await self.get_object()}


class FormView(mixins.RedirectResponseMixin, TemplateView):

    form_class = None

    def initialize(self):
        super().initialize()
        self.form_class = self.get_form_class()
        self.redirect_url = self.get_redirect_url()

        assert self.form_class, (
            'FormView requires either a definition of '
            '"form_class" or an implementation of "get_form_class()"'
        )

    def get_form_class(self):
        return self.form_class

    async def get_form_kwargs(self):
        return {'data': self.request.POST}

    async def get_form(self):
        return self.form_class(**await self.get_form_kwargs())

    async def post(self, *args, **kwargs):
        form = await self.get_form()

        try:
            await form.validate()
        except form.ValidationError as e:
            return await self.form_invalid(form, e.error)
        else:
            return await self.form_valid(form)

    async def form_valid(self, form):
        await form.save()
        return self.redirect(self.redirect_url)

    async def form_invalid(self, form, errors):
        self.render(self.template_name, form=form, errors=errors)


class CreateView(mixins.ModelResponseMixin, FormView):

    def get_form_class(self):
        return self.get_model()


class UpdateView(mixins.DetailResponseMixin, CreateView):

    async def get_form_kwargs(self):
        kwargs = await super().get_form_kwargs()
        kwargs['instance'] = await self.get_object()
        return kwargs


class DeleteView(mixins.RedirectResponseMixin,
                 mixins.DetailResponseMixin,
                 View):

    def initialize(self):
        super().initialize()
        self.redirect_url = self.get_redirect_url()

    async def delete(self, *args, **kwargs):
        await (await self.get_object()).delete()
        return self.redirect(self.redirect_url)
