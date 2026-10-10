"""The standard starter projects offered by the duplicate / change-owner / delete macros.

This is the single source of the list: the three descriptors declare
``"paramsPythonSetup": "starter_choices.py"`` and mark their starter parameter
``"getChoicesFromPython": true``; ``resource/starter_choices.py`` then serves
``STARTERS`` through :func:`starter_choices`.
"""
from typing import Dict, List

STARTERS: List[Dict[str, str]] = [
    {"value": "KO1COBUILD", "label": "Start 1 Cobuild"},
    {"value": "KO2EXPL", "label": "Start 2 Explore"},
    {"value": "KO3ML", "label": "Start 3 ML"},
    {"value": "KO4EVAL", "label": "Start 4 Evaluate"},
    {"value": "PROD_REVIEW", "label": "LLM - 상품 리뷰 분석"},
    {"value": "LLMPROMPTENGINEERING", "label": "LLM - Prompt Engineering"},
    {"value": "MULTIMODALRAG", "label": "LLM - Multimodal RAG"},
    {"value": "TUT_VISUAL_AGENTS", "label": "Visual Agents Tutorial"},
    {"value": "LOAN_ADVISOR_AGENT", "label": "대출 상담 어드바이저 에이전트"},
]

STARTER_KEYS: List[str] = [starter["value"] for starter in STARTERS]


def starter_choices(payload=None, config=None, plugin_config=None, inputs=None) -> Dict[str, List[Dict[str, str]]]:
    """Return value for a descriptor ``do()`` function (DSS dynamic select)."""
    return {"choices": list(STARTERS)}
