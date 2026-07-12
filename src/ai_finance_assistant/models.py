from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


class StatementParseError(ValueError):
    """PDF ekstre işlem tablosuna dönüştürülemediğinde fırlatılır."""


@dataclass(frozen=True)
class AnalysisBundle:
    raw_transactions: pd.DataFrame
    analysis_data: pd.DataFrame
    transaction_type_summary: pd.DataFrame
    category_summary: pd.DataFrame
    monthly_summary: pd.DataFrame
    latest_month: str
    latest_month_data: pd.DataFrame
    latest_month_total: float
    latest_month_category_summary: pd.DataFrame
    spending_findings: pd.DataFrame
    recurring_transactions: pd.DataFrame
    anomalies: pd.DataFrame
    budget_summary: pd.DataFrame
    health_score: int
    savings_potential: float
    previous_month_change_pct: float | None
    financial_commentary: str
    report_path: str
