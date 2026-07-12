"""Backward-compatible facade for AI Finans Asistanı V2.

New code lives under ``src/ai_finance_assistant``. Existing imports from
``finance_core`` continue to work for local users and earlier tests.
"""

from src.ai_finance_assistant import (
    AnalysisBundle,
    DEFAULT_BUDGETS,
    StatementParseError,
    analyze_statement,
    analyze_transactions,
    create_demo_transactions,
)
from src.ai_finance_assistant.parsing import (
    categorize_transaction,
    classify_transaction_type,
    extract_transaction_from_line,
    normalize_merchant,
    parse_turkish_amount,
    read_credit_card_statement,
)

_extract_transaction_from_line = extract_transaction_from_line

__all__ = [
    "AnalysisBundle",
    "DEFAULT_BUDGETS",
    "StatementParseError",
    "_extract_transaction_from_line",
    "analyze_statement",
    "analyze_transactions",
    "categorize_transaction",
    "classify_transaction_type",
    "create_demo_transactions",
    "normalize_merchant",
    "parse_turkish_amount",
    "read_credit_card_statement",
]
