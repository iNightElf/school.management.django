import importlib
from django.apps import AppConfig


class AiQueryConfig(AppConfig):
    name = 'ai_query'

    def ready(self):
        importlib.import_module('ai_query.handlers')
