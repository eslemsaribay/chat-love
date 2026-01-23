"""Prompt templates and examples package."""

from .system_instructions import (
    get_system_instruction,
    list_available_templates,
    SYSTEM_INSTRUCTIONS
)
from .examples import get_few_shot_examples, get_examples_enabled, FEW_SHOT_EXAMPLES

__all__ = [
    "get_system_instruction",
    "list_available_templates",
    "SYSTEM_INSTRUCTIONS",
    "get_few_shot_examples",
    "get_examples_enabled",
    "FEW_SHOT_EXAMPLES",
]
