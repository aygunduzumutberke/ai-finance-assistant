from __future__ import annotations

from typing import Any, Mapping

import numpy as np
import pandas as pd

from .models import StatementParseError
from .parsing import categorize_transaction

DEFAULT_BUDGETS: dict[str, float] = {
    "Yemek": 6000.0,
    "Kafe": 2000.0,
    "Market": 5000.0,
    "Ulaşım": 3000.0,
    "E-Ticaret": 4000.0,
    "Giyim": 4000.0,
    "Abonelik / Dijital": 1500.0,
    "Kişisel Bakım": 2000.0,
    "Eğlence": 2500.0,
}

DISCRETIONARY_CATEGORIES = {
    "Yemek",
    "Kafe",
    "E-Ticaret",
    "Giyim",
    "Abonelik / Dijital",
    "Eğlence",
    "Tütün",
}

FINDING_COLUMNS = ["Tespit", "Kategori", "Açıklama", "Tutar", "Risk_Seviyesi"]


def prepare_analysis_data(
    raw_transactions: pd.DataFrame,
    category_overrides: Mapping[str, str] | None = None,
) -> pd.DataFrame:
    data = raw_transactions[
        raw_transactions["Islem_Tipi"].isin(["Harcama", "Faiz / Masraf"])
    ].copy()
    if data.empty:
        raise StatementParseError("Analize dahil edilebilecek harcama işlemi bulunamadı.")

    data["Tutar"] = data["Tutar"].abs()
    data["Kategori"] = data["Açıklama"].apply(categorize_transaction)
    if category_overrides:
        data["Kategori"] = data.apply(
            lambda row: category_overrides.get(str(row["Merchant"]), row["Kategori"]),
            axis=1,
        )
    data["Ay"] = data["Tarih"].dt.to_period("M").astype(str)
    return data


def build_analysis_tables(
    raw_transactions: pd.DataFrame,
    category_overrides: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    data = prepare_analysis_data(raw_transactions, category_overrides)

    transaction_type_summary = (
        raw_transactions.groupby("Islem_Tipi", as_index=False)
        .agg(
            Toplam_Tutar=("Tutar", "sum"),
            Islem_Sayisi=("Tutar", "count"),
            Ortalama_Tutar=("Tutar", "mean"),
        )
    )
    transaction_type_summary["Ortalama_Tutar"] = transaction_type_summary[
        "Ortalama_Tutar"
    ].round(2)

    category_summary = (
        data.groupby("Kategori", as_index=False)
        .agg(
            Toplam_Harcama=("Tutar", "sum"),
            Islem_Sayisi=("Tutar", "count"),
            Ortalama_Harcama=("Tutar", "mean"),
        )
        .sort_values("Toplam_Harcama", ascending=False)
        .reset_index(drop=True)
    )
    category_summary["Ortalama_Harcama"] = category_summary[
        "Ortalama_Harcama"
    ].round(2)

    monthly_summary = (
        data.groupby("Ay", as_index=False)
        .agg(
            Toplam_Harcama=("Tutar", "sum"),
            Islem_Sayisi=("Tutar", "count"),
            Ortalama_Islem_Tutari=("Tutar", "mean"),
        )
        .sort_values("Ay")
        .reset_index(drop=True)
    )
    monthly_summary["Ortalama_Islem_Tutari"] = monthly_summary[
        "Ortalama_Islem_Tutari"
    ].round(2)

    latest_month = str(data["Ay"].max())
    latest_month_data = data[data["Ay"] == latest_month].copy()
    latest_month_total = float(latest_month_data["Tutar"].sum())

    latest_month_category_summary = (
        latest_month_data.groupby("Kategori", as_index=False)
        .agg(
            Toplam_Harcama=("Tutar", "sum"),
            Islem_Sayisi=("Tutar", "count"),
            Ortalama_Harcama=("Tutar", "mean"),
        )
        .sort_values("Toplam_Harcama", ascending=False)
        .reset_index(drop=True)
    )
    latest_month_category_summary["Ortalama_Harcama"] = (
        latest_month_category_summary["Ortalama_Harcama"].round(2)
    )
    latest_month_category_summary["Harcama_Orani_%"] = (
        latest_month_category_summary["Toplam_Harcama"]
        / latest_month_total
        * 100
    ).round(2)

    previous_month_change_pct: float | None = None
    if len(monthly_summary) >= 2:
        previous_total = float(monthly_summary.iloc[-2]["Toplam_Harcama"])
        if previous_total > 0:
            previous_month_change_pct = round(
                (latest_month_total - previous_total) / previous_total * 100,
                2,
            )

    return {
        "analysis_data": data,
        "transaction_type_summary": transaction_type_summary,
        "category_summary": category_summary,
        "monthly_summary": monthly_summary,
        "latest_month": latest_month,
        "latest_month_data": latest_month_data,
        "latest_month_total": latest_month_total,
        "latest_month_category_summary": latest_month_category_summary,
        "previous_month_change_pct": previous_month_change_pct,
    }


def detect_recurring_transactions(data: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "Merchant",
        "Kategori",
        "Ay_Sayisi",
        "Islem_Sayisi",
        "Ortalama_Tutar",
        "Tahmini_Aylik_Tutar",
        "Guven",
    ]
    if data.empty:
        return pd.DataFrame(columns=columns)

    records: list[dict[str, Any]] = []
    for merchant, group in data.groupby("Merchant"):
        if len(group) < 2:
            continue
        month_count = int(group["Ay"].nunique())
        mean_amount = float(group["Tutar"].mean())
        variation = float(group["Tutar"].std(ddof=0) / mean_amount) if mean_amount else 1.0
        is_subscription_category = (group["Kategori"] == "Abonelik / Dijital").any()
        recurring = month_count >= 2 or (is_subscription_category and len(group) >= 2)
        if not recurring or variation > 0.35:
            continue

        confidence = "Yüksek" if month_count >= 3 and variation <= 0.15 else "Orta"
        records.append(
            {
                "Merchant": merchant,
                "Kategori": group["Kategori"].mode().iat[0],
                "Ay_Sayisi": month_count,
                "Islem_Sayisi": len(group),
                "Ortalama_Tutar": round(mean_amount, 2),
                "Tahmini_Aylik_Tutar": round(mean_amount, 2),
                "Guven": confidence,
            }
        )

    return (
        pd.DataFrame(records, columns=columns)
        .sort_values("Tahmini_Aylik_Tutar", ascending=False)
        .reset_index(drop=True)
        if records
        else pd.DataFrame(columns=columns)
    )


def detect_anomalies(latest_month_data: pd.DataFrame) -> pd.DataFrame:
    columns = ["Tarih", "Merchant", "Kategori", "Tutar", "Neden", "Sapma_Skoru"]
    if len(latest_month_data) < 4:
        return pd.DataFrame(columns=columns)

    amounts = latest_month_data["Tutar"].astype(float)
    median = float(amounts.median())
    mad = float(np.median(np.abs(amounts - median)))
    q1, q3 = amounts.quantile([0.25, 0.75])
    iqr = float(q3 - q1)
    robust_scores = 0.6745 * (amounts - median) / mad if mad > 0 else pd.Series(0.0, index=amounts.index)
    threshold = max(float(q3 + 1.5 * iqr), median * 2.5, 1000.0)

    mask = (amounts > threshold) & (robust_scores.abs() >= 2.5)
    anomalies = latest_month_data.loc[mask, ["Tarih", "Merchant", "Kategori", "Tutar"]].copy()
    if anomalies.empty:
        return pd.DataFrame(columns=columns)

    anomalies["Neden"] = "Aylık tipik işlem seviyesinin belirgin üzerinde"
    anomalies["Sapma_Skoru"] = robust_scores.loc[anomalies.index].round(2).values
    return anomalies.sort_values("Tutar", ascending=False).reset_index(drop=True)


def build_budget_summary(
    category_summary: pd.DataFrame,
    budgets: Mapping[str, float] | None = None,
) -> pd.DataFrame:
    budget_map = dict(DEFAULT_BUDGETS)
    if budgets:
        budget_map.update({key: float(value) for key, value in budgets.items() if float(value) > 0})

    rows: list[dict[str, Any]] = []
    spent_map = category_summary.set_index("Kategori")["Toplam_Harcama"].to_dict()
    for category, budget in budget_map.items():
        spent = float(spent_map.get(category, 0.0))
        usage = spent / budget * 100 if budget else 0.0
        rows.append(
            {
                "Kategori": category,
                "Butce": round(budget, 2),
                "Harcama": round(spent, 2),
                "Kalan": round(budget - spent, 2),
                "Kullanim_%": round(usage, 2),
                "Durum": "Aşıldı" if usage > 100 else "Yaklaşıyor" if usage >= 80 else "İyi",
            }
        )
    return pd.DataFrame(rows).sort_values("Kullanim_%", ascending=False).reset_index(drop=True)


def detect_spending_patterns(
    latest_month_data: pd.DataFrame,
    category_summary: pd.DataFrame,
    latest_month_total: float,
    budget_summary: pd.DataFrame,
    recurring: pd.DataFrame,
    anomalies: pd.DataFrame,
) -> pd.DataFrame:
    findings: list[dict[str, Any]] = []
    average = float(latest_month_data["Tutar"].mean())

    def add(title: str, category: str, explanation: str, amount: float, risk: str) -> None:
        findings.append(
            {
                "Tespit": title,
                "Kategori": category,
                "Açıklama": explanation,
                "Tutar": round(float(amount), 2),
                "Risk_Seviyesi": risk,
            }
        )

    top = category_summary.iloc[0]
    if float(top["Harcama_Orani_%"]) >= 25:
        add(
            "Kategori yoğunlaşması",
            str(top["Kategori"]),
            f"Toplam harcamanın %{top['Harcama_Orani_%']} kısmı tek kategoride.",
            top["Toplam_Harcama"],
            "Orta",
        )

    small = latest_month_data[latest_month_data["Tutar"] < 300]
    if len(small) >= 8:
        small_total = float(small["Tutar"].sum())
        add(
            "Küçük ama sık harcamalar",
            "Genel",
            f"300 TL altı {len(small)} işlem toplam {small_total:.2f} TL.",
            small_total,
            "Düşük / Orta",
        )

    interest = category_summary[category_summary["Kategori"] == "Faiz / Masraf"]
    if not interest.empty and float(interest.iloc[0]["Toplam_Harcama"]) > 0:
        row = interest.iloc[0]
        add(
            "Faiz / masraf oluşmuş",
            "Faiz / Masraf",
            f"Toplam faiz ve masraf tutarı {row['Toplam_Harcama']:.2f} TL.",
            row["Toplam_Harcama"],
            "Yüksek",
        )

    for _, row in budget_summary[budget_summary["Durum"] == "Aşıldı"].iterrows():
        add(
            "Kategori bütçesi aşıldı",
            str(row["Kategori"]),
            f"Bütçe %{row['Kullanim_%']:.1f} oranında kullanıldı.",
            max(float(row["Harcama"] - row["Butce"]), 0.0),
            "Yüksek" if row["Kullanim_%"] >= 130 else "Orta",
        )

    if not recurring.empty:
        recurring_total = float(recurring["Tahmini_Aylik_Tutar"].sum())
        add(
            "Düzenli ödeme yükü",
            "Abonelik / Düzenli Ödeme",
            f"{len(recurring)} düzenli ödeme adayı, tahmini aylık toplam {recurring_total:.2f} TL.",
            recurring_total,
            "Orta",
        )

    if not anomalies.empty:
        add(
            "Olağandışı yüksek işlemler",
            "Genel",
            f"{len(anomalies)} işlem tipik aylık işlem seviyesinin belirgin üzerinde.",
            anomalies["Tutar"].sum(),
            "Orta",
        )

    expensive = category_summary[category_summary["Ortalama_Harcama"] > average * 1.5]
    for _, row in expensive.head(3).iterrows():
        add(
            "Yüksek ortalama işlem tutarı",
            str(row["Kategori"]),
            f"Kategori ortalaması {row['Ortalama_Harcama']:.2f} TL.",
            row["Toplam_Harcama"],
            "Düşük / Orta",
        )

    return pd.DataFrame(findings, columns=FINDING_COLUMNS)


def calculate_savings_potential(
    latest_month_data: pd.DataFrame,
    budget_summary: pd.DataFrame,
    recurring: pd.DataFrame,
) -> float:
    discretionary = latest_month_data[
        latest_month_data["Kategori"].isin(DISCRETIONARY_CATEGORIES)
    ]["Tutar"].sum()
    budget_overage = budget_summary.loc[
        budget_summary["Kalan"] < 0, "Kalan"
    ].abs().sum()
    recurring_candidate = recurring["Tahmini_Aylik_Tutar"].sum() if not recurring.empty else 0.0
    potential = discretionary * 0.10 + budget_overage * 0.25 + recurring_candidate * 0.10
    return round(float(potential), 2)


def calculate_health_score(
    latest_month_total: float,
    budget_summary: pd.DataFrame,
    findings: pd.DataFrame,
    previous_month_change_pct: float | None,
) -> int:
    score = 100.0
    exceeded = budget_summary[budget_summary["Durum"] == "Aşıldı"]
    score -= min(len(exceeded) * 6, 24)

    risks = findings["Risk_Seviyesi"].value_counts().to_dict() if not findings.empty else {}
    score -= risks.get("Yüksek", 0) * 8
    score -= risks.get("Orta", 0) * 4
    score -= risks.get("Düşük / Orta", 0) * 2

    if previous_month_change_pct is not None:
        if previous_month_change_pct > 30:
            score -= 12
        elif previous_month_change_pct > 15:
            score -= 6
        elif previous_month_change_pct < -10:
            score += 4

    if latest_month_total <= 0:
        score = 0
    return int(max(0, min(100, round(score))))
