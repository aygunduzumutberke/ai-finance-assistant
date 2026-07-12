from __future__ import annotations

import tempfile
import traceback
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from finance_core import AnalysisBundle, StatementParseError, analyze_statement


st.set_page_config(
    page_title="AI Finans Asistanı",
    page_icon="💳",
    layout="wide",
)


def format_try(amount: float) -> str:
    return f"{amount:,.2f} TL".replace(",", "X").replace(".", ",").replace("X", ".")


def display_frame(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    for column in result.columns:
        if ("Tutar" in column or "Harcama" in column) and pd.api.types.is_numeric_dtype(result[column]):
            result[column] = result[column].map(format_try)
    return result


def save_result_to_session(result: AnalysisBundle) -> None:
    st.session_state["analysis_result"] = result
    st.session_state["report_bytes"] = Path(result.report_path).read_bytes()
    st.session_state["report_name"] = Path(result.report_path).name


with st.sidebar:
    st.title("💳 AI Finans Asistanı")
    st.write("PDF kredi kartı ekstresinden otomatik harcama analizi üretir.")
    st.divider()
    st.subheader("Nasıl kullanılır?")
    st.write("1. PDF ekstreni yükle.")
    st.write("2. Analiz butonuna bas.")
    st.write("3. Dashboard ve tespitleri incele.")
    st.write("4. Excel raporunu indir.")
    st.divider()
    st.subheader("Gizlilik")
    st.caption(
        "Yüklenen dosya yalnızca analiz sırasında geçici klasörde tutulur. "
        "Uygulama kodu dosyayı kalıcı olarak saklamaz."
    )
    st.divider()
    st.caption(
        "Bu uygulama kural tabanlı bir prototiptir ve profesyonel finansal "
        "danışmanlık yerine geçmez."
    )


st.title("AI Finans Asistanı")
st.write(
    "Kredi kartı ekstresini yükle; işlem sınıflandırması, kategori analizi, "
    "harcama davranışı tespitleri, finans yorumu ve Excel dashboard raporu oluşsun."
)

uploaded_file = st.file_uploader(
    "PDF kredi kartı ekstresini yükle",
    type=["pdf"],
    help="Metin tabanlı PDF ekstreler desteklenir. Taranmış görüntü PDF'lerde OCR yoktur.",
)

if uploaded_file is not None:
    st.success(f"Dosya hazır: {uploaded_file.name}")

    if st.button("Analiz Et ve Dashboard Oluştur", type="primary", use_container_width=True):
        try:
            with st.spinner("Ekstre okunuyor ve rapor hazırlanıyor..."):
                with tempfile.TemporaryDirectory() as temp_dir:
                    pdf_path = Path(temp_dir) / "statement.pdf"
                    pdf_path.write_bytes(uploaded_file.getbuffer())
                    result = analyze_statement(pdf_path=pdf_path, output_dir=temp_dir)
                    save_result_to_session(result)
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

result: AnalysisBundle | None = st.session_state.get("analysis_result")

if result is None:
    st.info("Başlamak için bir PDF kredi kartı ekstresi yükle.")
    st.stop()

latest = result.latest_month_category_summary
findings = result.spending_findings
average_transaction = result.latest_month_total / len(result.latest_month_data) if len(result.latest_month_data) else 0
top_category = str(latest.iloc[0]["Kategori"])

st.divider()
dashboard_tab, tables_tab, commentary_tab, report_tab = st.tabs(
    ["Dashboard", "Detay Tablolar", "Finans Yorumu", "Excel Raporu"]
)

with dashboard_tab:
    st.subheader(f"Genel Özet · {result.latest_month}")
    column_1, column_2, column_3, column_4, column_5 = st.columns(5)
    column_1.metric("Toplam Harcama", format_try(result.latest_month_total))
    column_2.metric("İşlem Sayısı", len(result.latest_month_data))
    column_3.metric("Ortalama İşlem", format_try(average_transaction))
    column_4.metric("Tespit Sayısı", len(findings))
    column_5.metric("En Yüksek Kategori", top_category)

    st.subheader("Kategori Bazlı Harcama")
    bar_chart = px.bar(
        latest,
        x="Kategori",
        y="Toplam_Harcama",
        text="Toplam_Harcama",
        title="Kategori Bazlı Toplam Harcama",
    )
    bar_chart.update_traces(texttemplate="%{text:,.2f}", textposition="outside")
    bar_chart.update_layout(xaxis_title="Kategori", yaxis_title="Toplam Harcama (TL)")
    st.plotly_chart(bar_chart, use_container_width=True)

    left, right = st.columns(2)
    with left:
        pie_chart = px.pie(
            latest,
            names="Kategori",
            values="Toplam_Harcama",
            title="Kategori Harcama Dağılımı",
        )
        st.plotly_chart(pie_chart, use_container_width=True)

    with right:
        line_chart = px.line(
            result.monthly_summary,
            x="Ay",
            y="Toplam_Harcama",
            markers=True,
            title="Aylık Harcama Trendi",
        )
        line_chart.update_layout(xaxis_title="Ay", yaxis_title="Toplam Harcama (TL)")
        st.plotly_chart(line_chart, use_container_width=True)

    st.subheader("Dikkat Edilmesi Gereken Harcama Davranışları")
    if findings.empty:
        st.info("Belirgin bir harcama riski tespit edilmedi.")
    else:
        st.dataframe(display_frame(findings), use_container_width=True, hide_index=True)

with tables_tab:
    st.subheader("Son Ay Kategori Özeti")
    st.dataframe(display_frame(result.latest_month_category_summary), use_container_width=True, hide_index=True)

    st.subheader("Aylık Özet")
    st.dataframe(display_frame(result.monthly_summary), use_container_width=True, hide_index=True)

    st.subheader("İşlem Tipi Özeti")
    st.dataframe(display_frame(result.transaction_type_summary), use_container_width=True, hide_index=True)

    st.subheader("Analize Dahil Edilen İşlemler")
    st.dataframe(display_frame(result.analysis_data), use_container_width=True, hide_index=True)

with commentary_tab:
    st.subheader("Finans Yorumu")
    st.text_area("Aylık değerlendirme", result.financial_commentary, height=560, disabled=True)

with report_tab:
    st.subheader("Excel Dashboard Raporu")
    st.write("Tüm analiz tablolarını ve Excel içi dashboard'u içeren raporu indirebilirsin.")
    st.download_button(
        "Excel Raporunu İndir",
        data=st.session_state["report_bytes"],
        file_name=st.session_state["report_name"],
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
