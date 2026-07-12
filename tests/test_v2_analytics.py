from finance_core import DEFAULT_BUDGETS, analyze_transactions, create_demo_transactions
from src.ai_finance_assistant.analytics import (
    build_analysis_tables,
    build_budget_summary,
    calculate_health_score,
    detect_anomalies,
    detect_recurring_transactions,
)


def test_demo_contains_multiple_months() -> None:
    demo = create_demo_transactions()
    tables = build_analysis_tables(demo)
    assert len(tables["monthly_summary"]) == 3
    assert tables["previous_month_change_pct"] is not None


def test_recurring_payments_detected() -> None:
    demo = create_demo_transactions()
    tables = build_analysis_tables(demo)
    recurring = detect_recurring_transactions(tables["analysis_data"])
    merchants = set(recurring["Merchant"])
    assert any("NETFLIX" in merchant for merchant in merchants)
    assert any("SPOTIFY" in merchant for merchant in merchants)


def test_anomaly_detected() -> None:
    demo = create_demo_transactions()
    tables = build_analysis_tables(demo)
    anomalies = detect_anomalies(tables["latest_month_data"])
    assert not anomalies.empty
    assert anomalies["Tutar"].max() >= 12999


def test_budget_summary_and_health_score() -> None:
    demo = create_demo_transactions()
    tables = build_analysis_tables(demo)
    budget_summary = build_budget_summary(
        tables["latest_month_category_summary"],
        {**DEFAULT_BUDGETS, "Yemek": 1000.0},
    )
    assert "Aşıldı" in set(budget_summary["Durum"])
    score = calculate_health_score(
        tables["latest_month_total"],
        budget_summary,
        findings=budget_summary.iloc[0:0].rename(columns={"Durum": "Risk_Seviyesi"}),
        previous_month_change_pct=tables["previous_month_change_pct"],
    )
    assert 0 <= score <= 100


def test_full_demo_pipeline_creates_report(tmp_path) -> None:
    result = analyze_transactions(
        create_demo_transactions(),
        output_dir=tmp_path,
        budgets=DEFAULT_BUDGETS,
    )
    assert result.health_score <= 100
    assert result.savings_potential >= 0
    assert result.report_path.endswith(".xlsx")
