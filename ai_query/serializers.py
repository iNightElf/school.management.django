from rest_framework import serializers


class QuerySerializer(serializers.Serializer):
    query = serializers.CharField(min_length=1, max_length=1000)


class QueryResultSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=['table', 'summary', 'clarification', 'error'])
    explanation = serializers.CharField()
    data = serializers.ListField(default=list)
    columns = serializers.ListField(child=serializers.CharField(), default=list)
    confidence = serializers.FloatField()
    meta = serializers.DictField(default=dict)
