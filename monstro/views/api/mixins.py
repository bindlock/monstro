# coding=utf-8


class ModelAPIMixin(object):

    async def options(self, *args, **kwargs):
        self.set_status(200)
        self.finish({
            'fields': await self.form_class.get_metadata(),
            'lookup_field': self.lookup_field,
            'search_fields': self.search_fields,
            'search_query_argument': self.search_query_argument
        })


class CreateAPIMixin(ModelAPIMixin):

    async def post(self, *args, **kwargs):
        try:
            instance = await self.model.objects.create(**self.data)
        except self.model.ValidationError as e:
            if isinstance(e.error, str):
                return self.send_error(400, reason=e.error)

            return self.send_error(400, details=e.error)

        self.set_status(201)
        self.finish(await self.form_class(instance=instance).serialize())


class UpdateAPIMixin(ModelAPIMixin):

    async def put(self, *args, **kwargs):
        instance = await self.get_object()

        try:
            await instance.update(**self.data)
        except self.model.ValidationError as e:
            if isinstance(e.error, str):
                return self.send_error(400, reason=e.error)

            return self.send_error(400, details=e.error)

        self.set_status(200)
        self.finish(await self.form_class(instance=instance).serialize())

    async def patch(self, *args, **kwargs):
        await self.put()


class DeleteAPIMixin(ModelAPIMixin):

    async def delete(self, *args, **kwargs):
        instance = await self.get_object()

        await instance.delete()

        self.set_status(200)
        self.finish({})
