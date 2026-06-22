REGISTRY = {}


def ai_function(*, name, description, permissions, parameters, result_columns):
    def decorator(fn):
        REGISTRY[name] = {
            'name': name,
            'description': description,
            'permissions': permissions,
            'parameters': parameters,
            'result_columns': result_columns,
            'handler': fn,
        }
        return fn
    return decorator
