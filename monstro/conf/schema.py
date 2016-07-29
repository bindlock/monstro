# coding=utf-8

from monstro import serializers


class SettingsSchema(serializers.Serializer):

    secret_key = serializers.StringField()
    debug = serializers.BooleanField()
    mongodb_uri = serializers.StringField()
    mongodb_database = serializers.StringField()

    modules = serializers.ArrayField(
        field=serializers.StringField(), required=False, default=[]
    )
    tornado_settings = serializers.MapField(required=False, default={})
    test_args = serializers.ArrayField(required=False, default=[])
