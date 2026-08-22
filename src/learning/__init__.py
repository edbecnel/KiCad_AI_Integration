"""AERF learning loop — library promotion from staged analysis."""

from learning.family_promotion import (
    PromotionResult,
    check_promotion_gates,
    promote_family_to_library,
    try_auto_promote,
)

__all__ = [
    "PromotionResult",
    "check_promotion_gates",
    "promote_family_to_library",
    "try_auto_promote",
]
