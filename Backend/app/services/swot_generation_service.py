"""Validate AI findings before storing them in the existing text columns."""
SWOT_FIELDS = ('strengths', 'weaknesses', 'opportunities', 'threats')


def normalize_ai_swot(result):
    if not isinstance(result, dict):
        raise ValueError('The AI SWOT must be a JSON object')
    normalized = {}
    for field in SWOT_FIELDS:
        items = result.get(field, [])
        if not isinstance(items, list) or any(not isinstance(item, str) for item in items):
            raise ValueError(f'The AI SWOT field {field} must be a list of text findings')
        normalized[field] = '\n'.join(item.strip() for item in items if item.strip())
    return normalized
