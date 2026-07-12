"""AI Finans Asistanı V2 public API."""

from .analytics import DEFAULT_BUDGETS
from .demo import create_demo_transactions
from .models import AnalysisBundle, StatementParseError
from .pipeline import analyze_statement, analyze_transactions

__all__ = [
    "AnalysisBundle",
    "DEFAULT_BUDGETS",
    "StatementParseError",
    "analyze_statement",
    "analyze_transactions",
    "create_demo_transactions",
]

__version__ = "2.0.0"
