from accounts.permissions import has_permission


def filter_functions_for_user(user, registry):
    allowed = []
    for name, entry in registry.items():
        if all(has_permission(user, perm) for perm in entry['permissions']):
            allowed.append(entry)
    return allowed
