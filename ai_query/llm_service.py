from .provider import get_provider


def call_ai_function(system_prompt, user_query, functions):
    return get_provider().execute(system_prompt, user_query, functions)


def build_function_definitions(registry_slice):
    return get_provider().build_function_definitions(registry_slice)
