"""LLM-based complaint classification for FlowDesk.

Analyses the free-text complaint description and returns a structured
``{"category": ..., "priority": ...}`` dict whose values are guaranteed
to be valid per ``constants.CATEGORIES`` and ``constants.PRIORITIES``.
"""

from __future__ import annotations

from backend import constants


def classify_complaint(description: str) -> dict:
    """Classify a complaint description into a category and priority.

    Parameters
    ----------
    description:
        The raw, user-supplied complaint text.

    Returns
    -------
    dict
        ``{"category": <str>, "priority": <str>}`` where both values
        are drawn from the canonical allowed sets in ``constants``.
    """
    from backend.llm import call_gemini

    prompt = f"""You are the Classification Agent for FlowDesk.
    Analyze the following student complaint and classify it into a category and a priority level.

    Allowed Categories:
    {', '.join(constants.CATEGORIES)}

    Allowed Priorities:
    {', '.join(constants.PRIORITIES)}

    Complaint:
    "{description}"
    """

    schema = {
        "type": "OBJECT",
        "properties": {
            "category": {
                "type": "STRING",
                "description": f"The category of the complaint. Must be exactly one of: {list(constants.CATEGORIES)}"
            },
            "priority": {
                "type": "STRING",
                "description": f"The priority of the complaint. Must be exactly one of: {list(constants.PRIORITIES)}"
            }
        },
        "required": ["category", "priority"]
    }

    result = call_gemini(prompt, response_schema=schema)
    
    category = _validate_category(result.get("category", ""))
    priority = _validate_priority(result.get("priority", ""))
    
    return {"category": category, "priority": priority}


def _validate_category(category: str) -> str:
    """Sanitise a predicted category string.

    If *category* is not in ``constants.CATEGORIES``, falls back to
    ``"Other"``.
    """
    if not category:
        return "Other"
    
    cleaned = category.strip()
    if cleaned not in constants.CATEGORIES:
        return "Other"
    return cleaned


def _validate_priority(priority: str) -> str:
    """Sanitise a predicted priority string.

    If *priority* is not in ``constants.PRIORITIES``, falls back to
    ``"Medium"``.
    """
    if not priority:
        return "Medium"
        
    cleaned = priority.strip()
    if cleaned not in constants.PRIORITIES:
        return "Medium"
    return cleaned

