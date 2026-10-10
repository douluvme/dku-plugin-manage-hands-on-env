"""The single source of the standard starter-project list.

The macros 1-1 (duplicate), 1-2 (change owner) and 2-1 (delete) expose this
list as the choices of their project-key parameter through DSS dynamic
choices (``"getChoicesFromPython": true`` in their ``runnable.json`` plus a
module-level ``do()`` in their ``runnable.py``). Add or rename a starter
project here and all three macros follow.
"""

STARTERS = [
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


def starter_choices():
    """The payload DSS expects from a ``do()`` dynamic-choices function."""
    return {"choices": [dict(entry) for entry in STARTERS]}
