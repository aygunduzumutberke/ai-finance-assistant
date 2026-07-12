from __future__ import annotations

import tempfile
import traceback
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from finance_core import (
    AnalysisBundle,
    DEFAULT_BUDGETS,
    StatementParseError,
    analyze_statement,
    analyze_transactions,
    create_demo_transactions,
)

st.set_page_config(
    page_title="AI Finans Asistanı V2",
    page_icon="💳",
    layout="wide",
)

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 3rem;}
    [data-testid="stMetric"] {border: 1px solid rgba(128,128,128,.22); padding: 12px; border-radius: 12px;}
    .hero {padding: 1.25rem 1.4rem; border-radius: 16px; background: linear-gradient(120deg,#14213d,#264653); margin-bottom: 1rem;}
    .hero h1, .hero p {color: white; margin: 0;}
    .hero p {opacity: .86; margin-top: .45rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

CATEGORY_OPTIONS = [
    "Yemek", "Kafe", "Market", "Ulaşım", "E-Ticaret", "Giyim",
    "Abonelik / Dijital", "Kişisel Bakım", "Sağlık", "Eğlence",
    "Nakit Çekim", "Faiz / Masraf", "Tütün", "Diğer",
]


def format_try(amount: float) -> str:
    return f"{amount:,.2f} TL".replace(",", "X").replace(".", ",").replace("X", ".")


def display_frame(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in result.columns:
        if ("Tutar" in column or "Harcama" in column or column in {"Butce", "Kalan"}) and pd.api.types.is_numeric_dtype(result[column]):
            result[column] = result[column].map(format_try)
    return result


def save_result(result: AnalysisBundle, budgets: dict[str, float]) -> None:
    st.session_state["analysis_result"] = result
    st.session_state["report_bytes"] = Path(result.report_path).read_bytes()
    st.session_state["report_name"] = Path(result.report_path).name
    st.session_state["budgets"] = budgets


def run_analysis_from_transactions(
    transactions: pd.DataFrame,
    budgets: dict[str, float],
    overrides: dict[str, str] | None = None,
) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        result = analyze_transactions(
            transactions,
            output_dir=temp_dir,
            budgets=budgets,
            category_overrides=overrides,
        )
        save_result(result, budgets)


with st.sidebar:
    st.title("💳 AI Finans Asistanı V2")
    mode = st.radio("Çalışma modu", ["PDF Ekstre", "Demo Modu"], horizontal=False)
    st.caption("Demo modu tamamen kurgusal veri kullanır ve ürünün tüm özelliklerini gösterir.")
    st.divider()

    st.subheader("Aylık kategori bütçeleri")
    budgets: dict[str, float] = {}
    for category, default_value in DEFAULT_BUDGETS.items():
        budgets[category] = st.number_input(
            category,
            min_value=0.0,
            value=float(default_value),
            step=250.0,
            format="%.0f",
        )

    st.divider()
    st.subheader("Gizlilik")
    st.caption(
        "Yüklenen PDF geçici klasörde işlenir. Gerçek ekstreler ve oluşturulan Excel dosyaları repoya kaydedilmez."
    )
    st.caption("Analiz profesyonel finansal danışmanlık değildir.")


st.markdown(
    """
    <div class="hero">
      <h1>AI Finans Asistanı V2</h1>
      <p>PDF ekstre analizi, bütçe takibi, düzenli ödeme tespiti, anomali analizi, finansal sağlık puanı ve Excel dashboard.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if mode == "PDF Ekstre":
    uploaded_file = st.file_uploader(
        "PDF kredi kartı ekstresini yükle",
        type=["pdf"],
        help="Metin tabanlı PDF ekstreler desteklenir. Taranmış görüntü PDF'lerde OCR henüz yoktur.",
    )
    analyze_clicked = st.button(
        "Analiz Et ve V2 Dashboard Oluştur",
        type="primary",
        use_container_width=True,
        disabled=uploaded_file is None,
    )

    if analyze_clicked and uploaded_file is not None:
        try:
            with st.spinner("Ekstre okunuyor, bütçe ve davranış analizleri hazırlanıyor..."):
                with tempfile.TemporaryDirectory() as temp_dir:
                    pdf_path = Path(temp_dir) / "statement.pdf"
                    pdf_path.write_bytes(uploaded_file.getbuffer())
                    result = analyze_statement(
                        pdf_path=pdf_path,
                        output_dir=temp_dir,
                        budgets=budgets,
                    )
                    save_result(result, budgets)
            st.success("Analiz başarıyla tamamlandı.")
        except StatementParseError as exc:
            st.session_state.pop("analysis_result", None)
            st.error("Ekstre içerisinden işlem tablosu okunamadı.")
            st.warning(str(exc))
        except Exception as exc:
            st.session_state.pop("analysis_result", None)
            st.error("Analiz sırasında beklenmeyen bir hata oluştu.")
            st.code(str(exc))
            with st.expander("Teknik detay"):
                st.code(traceback.format_exc())
else:
    st.info("Demo modu gerçek kişi veya banka verisi içermez.")
    if st.button("Demo Dashboard'u Aç", type="primary", use_container_width=True):
        with st.spinner("Kurgusal demo verisi hazırlanıyor..."):
            run_analysis_from_transactions(create_demo_transactions(), budgets)
        st.success("Demo analizi hazır.")


result: AnalysisBundle | None = st.session_state.get("analysis_result")
if result is None:
    st.info("Analize başlamak için PDF yükle veya Demo Modu'nu çalıştır.")
    st.stop()

latest = result.latest_month_category_summary
findings = result.spending_findings
average_transaction = result.latest_month_total / max(len(result.latest_month_data), 1)
previous_change = result.previous_month_change_pct
previous_label = "Veri yok" if previous_change is None else f"%{previous_change:+.2f}"

st.divider()
metric_columns = st.columns(6)
metric_columns[0].metric("Toplam Harcama", format_try(result.latest_month_total))
metric_columns[1].metric("İşlem Sayısı", len(result.latest_month_data))
metric_columns[2].metric("Ortalama İşlem", format_try(average_transaction))
metric_columns[3].metric("Sağlık Puanı", f"{result.health_score}/100")
metric_columns[4].metric("Tasarruf Potansiyeli", format_try(result.savings_potential))
metric_columns[5].metric("Önceki Aya Göre", previous_label)

(
    dashboard_tab,
    budget_tab,
    recurring_tab,
    anomaly_tab,
    transactions_tab,
    correction_tab,
    commentary_tab,
    report_tab,
) = st.tabs(
    [
        "Dashboard", "Bütçe", "Düzenli Ödemeler", "Anomaliler",
        "İşlemler", "Kategori Düzeltme", "Finans Yorumu", "Excel Raporu",
    ]
)

with dashboard_tab:
    left, right = st.columns([1.6, 1])
    with left:
        bar_chart = px.bar(
            latest,
            x="Kategori",
            y="Toplam_Harcama",
            color="Harcama_Orani_%",
            text="Toplam_Harcama",
            title=f"{result.latest_month} · Kategori Bazlı Harcama",
        )
        bar_chart.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        bar_chart.update_layout(yaxis_title="Toplam Harcama (TL)", xaxis_title="")
        st.plotly_chart(bar_chart, use_container_width=True)
    with right:
        pie_chart = px.pie(
            latest,
            names="Kategori",
            values="Toplam_Harcama",
            hole=0.45,
            title="Harcama Dağılımı",
        )
        st.plotly_chart(pie_chart, use_container_width=True)

    line_chart = px.line(
        result.monthly_summary,
        x="Ay",
        y="Toplam_Harcama",
        markers=True,
        title="Aylık Harcama Trendi",
    )
    line_chart.update_layout(yaxis_title="Toplam Harcama (TL)", xaxis_title="Ay")
    st.plotly_chart(line_chart, use_container_width=True)

    st.subheader("Dikkat Edilmesi Gereken Davranışlar")
    if findings.empty:
        st.success("Belirgin bir riskli harcama davranışı tespit edilmedi.")
    else:
        st.dataframe(display_frame(findings), use_container_width=True, hide_index=True)

with budget_tab:
    budget_chart = px.bar(
        result.budget_summary,
        x="Kategori",
        y=["Butce", "Harcama"],
        barmode="group",
        title="Kategori Bütçesi ve Gerçekleşen Harcama",
    )
    st.plotly_chart(budget_chart, use_container_width=True)
    st.dataframe(display_frame(result.budget_summary), use_container_width=True, hide_index=True)

with recurring_tab:
    if result.recurring_transactions.empty:
        st.info("Düzenli ödeme adayı tespit edilmedi. En iyi sonuç için en az iki aylık veri gerekir.")
    else:
        st.metric(
            "Tahmini Aylık Düzenli Ödeme",
            format_try(float(result.recurring_transactions["Tahmini_Aylik_Tutar"].sum())),
        )
        st.dataframe(display_frame(result.recurring_transactions), use_container_width=True, hide_index=True)

with anomaly_tab:
    if result.anomalies.empty:
        st.success("Belirgin bir olağandışı yüksek işlem bulunmadı.")
    else:
        anomaly_chart = px.scatter(
            result.anomalies,
            x="Tarih",
            y="Tutar",
            size="Tutar",
            color="Kategori",
            hover_name="Merchant",
            title="Olağandışı Yüksek İşlemler",
        )
        st.plotly_chart(anomaly_chart, use_container_width=True)
        st.dataframe(display_frame(result.anomalies), use_container_width=True, hide_index=True)

with transactions_tab:
    selected_categories = st.multiselect(
        "Kategori filtresi",
        options=sorted(result.analysis_data["Kategori"].unique()),
        default=sorted(result.analysis_data["Kategori"].unique()),
    )
    filtered = result.analysis_data[result.analysis_data["Kategori"].isin(selected_categories)]
    st.dataframe(display_frame(filtered), use_container_width=True, hide_index=True)

with correction_tab:
    st.write("Yanlış sınıflandırılan merchant kategorilerini değiştirip analizi yeniden çalıştırabilirsin.")
    merchant_categories = (
        result.analysis_data.groupby("Merchant", as_index=False)
        .agg(Kategori=("Kategori", lambda values: values.mode().iat[0]), Islem_Sayisi=("Tutar", "count"), Toplam_Harcama=("Tutar", "sum"))
        .sort_values("Toplam_Harcama", ascending=False)
    )
    edited = st.data_editor(
        merchant_categories,
        use_container_width=True,
        hide_index=True,
        disabled=["Merchant", "Islem_Sayisi", "Toplam_Harcama"],
        column_config={
            "Kategori": st.column_config.SelectboxColumn("Kategori", options=CATEGORY_OPTIONS, required=True),
            "Toplam_Harcama": st.column_config.NumberColumn("Toplam Harcama", format="%.2f TL"),
        },
        key="category_editor",
    )
    if st.button("Kategori Düzeltmeleriyle Yeniden Analiz Et", use_container_width=True):
        overrides = dict(zip(edited["Merchant"], edited["Kategori"]))
        with st.spinner("Kategoriler güncelleniyor..."):
            run_analysis_from_transactions(
                result.raw_transactions,
                st.session_state.get("budgets", budgets),
                overrides=overrides,
            )
        st.success("Kategoriler ve tüm analizler güncellendi.")
        st.rerun()

with commentary_tab:
    st.text_area("Aylık değerlendirme", result.financial_commentary, height=650, disabled=True)

with report_tab:
    st.write("Tüm tabloları, bütçe analizini, düzenli ödemeleri, anomalileri ve Excel içi dashboard'u içerir.")
    st.download_button(
        "Excel V2 Raporunu İndir",
        data=st.session_state["report_bytes"],
        file_name=st.session_state["report_name"],
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )
