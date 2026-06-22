def validate_and_score(entry, args):
    schema = entry.get('parameters', {})
    properties = schema.get('properties', {})
    required = schema.get('required', [])

    validated = {}
    filled_required = 0

    for name, prop in properties.items():
        raw = args.get(name)
        if raw is None:
            if name in required:
                continue
            validated[name] = None
            continue

        ptype = prop.get('type', 'string')
        if ptype == 'string' and isinstance(raw, str):
            validated[name] = raw
        elif ptype == 'integer':
            try:
                validated[name] = int(raw)
            except (ValueError, TypeError):
                validated[name] = raw
        elif ptype == 'number':
            try:
                validated[name] = float(raw)
            except (ValueError, TypeError):
                validated[name] = raw
        elif ptype == 'boolean' and isinstance(raw, bool):
            validated[name] = raw
        else:
            validated[name] = str(raw)

        if name in required:
            filled_required += 1

    score = 1.0
    if required:
        score *= filled_required / len(required)
    score = max(0.0, min(1.0, score))

    return validated, score
