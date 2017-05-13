class ModelAPIMixin(object):

    async def options(self, *args, **kwargs):
        self.finish({
            'fields': await (await self.get_form_class()).get_options(),
            'lookup_field': await self.get_lookup_field(),
            'search_fields': await self.get_search_fields(),
            'search_query_argument': await self.get_search_query_argument()
        })


class CreateAPIMixin(ModelAPIMixin):

    async def post(self, *args, **kwargs):
        form = (await self.get_form_class())(data=self.data)

        try:
            await form.save()
        except form.ValidationError as e:
            if isinstance(e.error, str):
                return self.send_error(400, reason=e.error)

            return self.send_error(400, details=e.error)

        self.set_status(201)
        self.finish(await form.serialize())


class UpdateAPIMixin(ModelAPIMixin):

    async def put(self, *args, **kwargs):
        instance = await self.get_object()
        form = (await self.get_form_class())(instance=instance, data=self.data)

        try:
            await form.save()
        except form.ValidationError as e:
            if isinstance(e.error, str):
                return self.send_error(400, reason=e.error)

            return self.send_error(400, details=e.error)

        self.finish(await form.serialize())

    async def patch(self, *args, **kwargs):
        await self.put(*args, **kwargs)


class DeleteAPIMixin(ModelAPIMixin):

    async def delete(self, *args, **kwargs):
        await (await self.get_object()).delete()
