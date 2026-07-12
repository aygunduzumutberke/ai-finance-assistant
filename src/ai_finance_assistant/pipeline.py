from __future__ import annotations

from pathlib import Path
from typing import Mapping

import pandas as pd

from .analytics import (
    build_analysis_tables,
    build_budget_summary,
    calculate_health_score,
    calculate_savings_potential,
    detect_anomalies,
    detect_recurring_transactions,
    detect_spending_patterns,
)
from .models import AnalysisBundle
from .parsing import read_credit_card_statement
from .reporting import write_excel_report


def format_try(amount: float) -> str:
    return f"{amount:,.2f} TL".replace(",", "X").replace(".", ",").replace("X", ".")


def generate_financial_commentary(
    tables: dict,
    findings: pd.DataFrame,
    recurring: pd.DataFrame,
    anomalies: pd.DataFrame,
    budget_summary: pd.DataFrame,
    health_score: int,
    savings_potential: float,
) -> str:
    latest = tables["latest_month_category_summary"]
    top = latest.iloc[0]
    previous_change = tables["previous_month_change_pct"]

    lines = [
        "AI Finans Asistanı V2 - Aylık Finans Yorumu",
        "=" * 54,
        "",
        f"Analiz edilen ay: {tables['latest_month']}",
        f"Toplam harcama: {format_try(tables['latest_month_total'])}",
        f"Toplam işlem sayısı: {len(tables['latest_month_data'])}",
        f"Finansal sağlık puanı: {health_score}/100",
        f"Tahmini tasarruf potansiyeli: {format_try(savings_potential)}",
    ]

    if previous_change is None:
        lines.append("Önceki ay karşılaştırması: Yeterli veri yok")
    else:
        direction = "arttı" if previous_change > 0 else "azaldı"
        lines.append(f"Önceki aya göre toplam harcama: %{abs(previous_change):.2f} {direction}")

    lines.extend(
        [
            "",
            "Genel Değerlendirme",
            "-" * 24,
            (
                f"En yüksek kategori {top['Kategori']} oldu. "
                f"Bu kategoride {format_try(float(top['Toplam_Harcama']))} harcandı "
                f"ve toplamın %{top['Harcama_Orani_%']} kısmını oluşturdu."
            ),
            "",
            "Bütçe Durumu",
            "-" * 13,
        ]
    )

    exceeded = budget_summary[budget_summary["Durum"] == "Aşıldı"]
    approaching = budget_summary[budget_summary["Durum"] == "Yaklaşıyor"]
    if exceeded.empty and approaching.empty:
        lines.append("Tanımlı kategori bütçelerinde kritik bir aşım görünmüyor.")
    else:
        for _, row in exceeded.iterrows():
            lines.append(
                f"- {row['Kategori']}: bütçe %{row['Kullanim_%']:.1f} kullanıldı, "
                f"{format_try(abs(float(row['Kalan'])))} aşım var."
            )
        for _, row in approaching.iterrows():
            lines.append(
                f"- {row['Kategori']}: bütçenin %{row['Kullanim_%']:.1f} kısmı kullanıldı."
            )

    lines.extend(["", "Düzenli Ödemeler", "-" * 17])
    if recurring.empty:
        lines.append("Düzenli ödeme adayı tespit edilmedi.")
    else:
        lines.append(
            f"{len(recurring)} düzenli ödeme adayı var. Tahmini aylık toplam: "
            f"{format_try(float(recurring['Tahmini_Aylik_Tutar'].sum()))}."
        )
        for _, row in recurring.head(5).iterrows():
            lines.append(
                f"- {row['Merchant']}: yaklaşık {format_try(float(row['Tahmini_Aylik_Tutar']))} / ay"
            )

    lines.extend(["", "Olağandışı İşlemler", "-" * 20])
    if anomalies.empty:
        lines.append("Belirgin bir harcama anomalisi tespit edilmedi.")
    else:
        lines.append(f"{len(anomalies)} olağandışı yüksek işlem tespit edildi.")
        for _, row in anomalies.head(5).iterrows():
            lines.append(
                f"- {row['Merchant']} · {row['Kategori']}: {format_try(float(row['Tutar']))}"
            )

    lines.extend(["", "Dikkat Edilmesi Gereken Alanlar", "-" * 31])
    if findings.empty:
        lines.append("Belirgin bir riskli davranış tespit edilmedi.")
    else:
        for _, row in findings.iterrows():
            lines.extend(
                [
                    f"- {row['Tespit']} ({row['Risk_Seviyesi']})",
                    f"  {row['Açıklama']}",
                ]
            )

    lines.extend(
        [
            "",
            "Önerilen Sonraki Adım",
            "-" * 21,
            (
                "Bütçesi aşılmış kategorilerden başlayarak haftalık limit belirlemek, "
                "düzenli ödemeleri gözden geçirmek ve anomalileri tek tek doğrulamak faydalı olur."
            ),
            "",
            "Not: Bu analiz açıklanabilir, kural tabanlı bir prototiptir; profesyonel finansal danışmanlık değildir.",
        ]
    )
    return "\n".join(lines)


def analyze_transactions(
    raw_transactions: pd.DataFrame,
    output_dir: str | Path,
    budgets: Mapping[str, float] | None = None,
    category_overrides: Mapping[str, str] | None = None,
    report_prefix: str = "AI_Finans_Asistani_V2",
) -> AnalysisBundle:
    tables = build_analysis_tables(raw_transactions, category_overrides)
    recurring = detect_recurring_transactions(tables["analysis_data"])
    anomalies = detect_anomalies(tables["latest_month_data"])
    budget_summary = build_budget_summary(
        tables["latest_month_category_summary"], budgets
    )
    findings = detect_spending_patterns(
        tables["latest_month_data"],
        tables["latest_month_category_summary"],
        tables["latest_month_total"],
        budget_summary,
        recurring,
        anomalies,
    )
    savings_potential = calculate_savings_potential(
        tables["latest_month_data"], budget_summary, recurring
    )
    health_score = calculate_health_score(
        tables["latest_month_total"],
        budget_summary,
        findings,
        tables["previous_month_change_pct"],
    )
    commentary = generate_financial_commentary(
        tables,
        findings,
        recurring,
        anomalies,
        budget_summary,
        health_score,
        savings_potential,
    )

    output_path = Path(output_dir).resolve()
    output_path.mkdir(parents=True, exist_ok=True)
    report_path = output_path / f"{report_prefix}_{tables['latest_month']}.xlsx"
    write_excel_report(
        report_path,
        raw_transactions,
        tables,
        findings,
        recurring,
        anomalies,
        budget_summary,
        health_score,
        savings_potential,
        commentary,
    )

    return AnalysisBundle(
        raw_transactions=raw_transactions,
        analysis_data=tables["analysis_data"],
        transaction_type_summary=tables["transaction_type_summary"],
        category_summary=tables["category_summary"],
        monthly_summary=tables["monthly_summary"],
        latest_month=tables["latest_month"],
        latest_month_data=tables["latest_month_data"],
        latest_month_total=tables["latest_month_total"],
        latest_month_category_summary=tables["latest_month_category_summary"],
        spending_findings=findings,
        recurring_transactions=recurring,
        anomalies=anomalies,
        budget_summary=budget_summary,
        health_score=health_score,
        savings_potential=savings_potential,
        previous_month_change_pct=tables["previous_month_change_pct"],
        financial_commentary=commentary,
        report_path=str(report_path),
    )


def analyze_statement(
    pdf_path: str | Path,
    output_dir: str | Path | None = None,
    budgets: Mapping[str, float] | None = None,
    category_overrides: Mapping[str, str] | None = None,
) -> AnalysisBundle:
    raw_transactions = read_credit_card_statement(pdf_path)
    target_dir = Path(pdf_path).resolve().parent if output_dir is None else Path(output_dir)
    return analyze_transactions(
        raw_transactions,
        output_dir=target_dir,
        budgets=budgets,
        category_overrides=category_overrides,
    )
