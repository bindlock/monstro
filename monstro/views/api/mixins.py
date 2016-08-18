# coding=utf-8

import tornado.gen


class ModelAPIMixin(object):

    @tornado.gen.coroutine
    def options(self, *args, **kwargs):
        self.set_status(200)
        self.finish({
            'fields': (yield self.form_class.get_metadata()),
            'lookup_field': self.lookup_field
        })


class CreateAPIMixin(ModelAPIMixin):

    @tornado.gen.coroutine
    def post(self, *args, **kwargs):
        try:
            instance = yield self.model.objects.create(**self.data)
        except self.model.ValidationError as e:
            return self.send_error(400, details=e.error)

        self.set_status(201)
        self.finish((yield self.form_class(instance=instance).serialize()))


class UpdateAPIMixin(ModelAPIMixin):

    @tornado.gen.coroutine
    def put(self, *args, **kwargs):
        instance = yield self.get_object()

        try:
            yield instance.update(**self.data)
        except self.model.ValidationError as e:
            return self.send_error(400, details=e.error)

        self.set_status(200)
        self.finish((yield self.form_class(instance=instance).serialize()))

    @tornado.gen.coroutine
    def patch(self, *args, **kwargs):
        yield self.put()


class DeleteAPIMixin(ModelAPIMixin):

    @tornado.gen.coroutine
    def delete(self, *args, **kwargs):
        instance = yield self.get_object()

        yield instance.delete()

        self.set_status(200)
        self.finish({})
