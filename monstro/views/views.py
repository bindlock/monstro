# coding=utf-8

import tornado.web
import tornado.gen

from . import mixins


class View(tornado.web.RequestHandler):

    authentication = None

    def initialize(self):
        self.request.GET = {}
        self.request.POST = {}

        self.authentication = self.get_authentication()

    def get_authentication(self):
        return self.authentication

    @tornado.gen.coroutine
    def prepare(self):
        if self.authentication:
            self.current_user = yield self.authentication.authenticate(self)

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

    @tornado.gen.coroutine
    def get_context_data(self):
        return {}

    @tornado.gen.coroutine
    def get(self, *args, **kwargs):
        self.render(self.template_name, **(yield self.get_context_data()))


class ListView(mixins.ListResponseMixin, TemplateView):

    context_object_name = 'objects'

    @tornado.gen.coroutine
    def get_context_data(self):
        return {self.context_object_name: (yield self.paginate())}


class DetailView(mixins.DetailResponseMixin, TemplateView):

    context_object_name = 'object'

    @tornado.gen.coroutine
    def get_context_data(self):
        return {self.context_object_name: (yield self.get_object())}


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

    @tornado.gen.coroutine
    def get_form_kwargs(self):
        return {'data': self.request.POST}

    @tornado.gen.coroutine
    def get_form(self):
        return self.form_class(**(yield self.get_form_kwargs()))

    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        form = yield self.get_form()

        try:
            yield form.validate()
        except form.ValidationError as e:
            return (yield self.form_invalid(form, e.error))
        else:
            return (yield self.form_valid(form))

    @tornado.gen.coroutine
    def form_valid(self, form):
        yield form.save()
        return self.redirect(self.redirect_url)

    @tornado.gen.coroutine
    def form_invalid(self, form, errors):
        self.render(self.template_name, form=form, errors=errors)


class CreateView(mixins.ModelResponseMixin, FormView):

    def get_form_class(self):
        return self.get_model()


class UpdateView(mixins.DetailResponseMixin, CreateView):

    @tornado.gen.coroutine
    def get_form_kwargs(self):
        kwargs = yield super().get_form_kwargs()
        kwargs['instance'] = yield self.get_object()
        return kwargs


class DeleteView(mixins.RedirectResponseMixin,
                 mixins.DetailResponseMixin,
                 View):

    def initialize(self):
        super().initialize()
        self.redirect_url = self.get_redirect_url()

    @tornado.gen.coroutine
    def delete(self, *args, **kwargs):
        yield (yield self.get_object()).delete()
        return self.redirect(self.redirect_url)
