"""
Prompts module for Canto-beats.
"""

from prompts.cantonese_prompts import (
    BASIC_CORRECTION_PROMPT,
    COMPLEXITY_JUDGE_PROMPT,
    SIMPLE_PROCESS_PROMPT,
    FULL_PROCESS_PROMPT_V3,
    protect_proper_nouns,
    restore_proper_nouns,
    get_prompt_for_tier,
)

__all__ = [
    "BASIC_CORRECTION_PROMPT",
    "COMPLEXITY_JUDGE_PROMPT", 
    "SIMPLE_PROCESS_PROMPT",
    "FULL_PROCESS_PROMPT_V3",
    "protect_proper_nouns",
    "restore_proper_nouns",
    "get_prompt_for_tier",
]
