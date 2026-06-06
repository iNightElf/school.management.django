import re
from rest_framework import serializers


def to_camel_case(snake_str):
    parts = snake_str.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])


def to_snake_case(camel_str):
    return re.sub(r'([A-Z])', r'_\1', camel_str).lower()


class CamelCaseModelSerializer(serializers.ModelSerializer):
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        return {to_camel_case(k): v for k, v in ret.items()}

    def to_internal_value(self, data):
        snake_data = {}
        for k, v in data.items():
            snake_data[to_snake_case(k)] = v
        return super().to_internal_value(snake_data)
