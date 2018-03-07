import bson
import bson.errors

from monstro.db import Or, Regex


class RedirectResponseMixin(object):

    redirect_url = None
    permanent = True

    async def get_redirect_url(self):
        assert self.redirect_url, (
            'RedirectResponseMixin requires either a definition of '
            '"redirect_url" or an implementation of "get_redirect_url()"'
        )

        return self.redirect_url


class ModelResponseMixin(object):

    model = None

    async def get_model(self):
        assert self.model, (
            'ModelResponseMixin requires either a definition of '
            '"model" or an implementation of "get_model()"'
        )

        return self.model


class QuerysetResponseMixin(ModelResponseMixin):

    queryset = None

    async def get_queryset(self):
        model = await self.get_model()

        assert self.queryset or model, (
            'QuerysetResponseMixin requires either a definition of '
            '"queryset" or an implementation of "get_queryset()"'
        )

        return self.queryset or model.objects.filter()


class ListResponseMixin(QuerysetResponseMixin):

    paginator = None
    search_fields = None
    search_query_argument = 'q'

    async def get_paginator(self):
        return self.paginator

    async def get_search_fields(self):
        return self.search_fields or []

    async def get_search_query_argument(self):
        return self.search_query_argument

    async def filter_queryset(self, queryset, fields, query):
        query = Or(Regex({f: query for f in fields}))
        return queryset.filter(**query)

    async def paginate(self):
        paginator = await self.get_paginator()
        queryset = await self.get_queryset()
        fields = await self.get_search_fields()
        query_argument = await self.get_search_query_argument()
        query = self.get_query_argument(query_argument, '')

        if fields and query:
            queryset = await self.filter_queryset(queryset, fields, query)

        if paginator:
            paginator.bind(**self.request.GET)
            return await paginator.paginate(queryset)

        return queryset


class DetailResponseMixin(QuerysetResponseMixin):

    lookup_field = '_id'

    async def get_lookup_field(self):
        return self.lookup_field

    async def get_object(self):
        lookup_field = await self.get_lookup_field()
        value = self.path_kwargs.get(lookup_field)

        if lookup_field == '_id':
            try:
                value = bson.objectid.ObjectId(value)
            except bson.errors.InvalidId:
                return self.send_error(404)

        queryset = await self.get_queryset()

        try:
            return await queryset.get(**{lookup_field: value})
        except queryset.model.DoesNotExist:
            return self.send_error(404)
