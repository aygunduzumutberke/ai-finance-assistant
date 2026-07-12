from finance_core import (
    _extract_transaction_from_line,
    categorize_transaction,
    classify_transaction_type,
    parse_turkish_amount,
)


def test_parse_turkish_amount() -> None:
    assert parse_turkish_amount("1.450,00") == 1450.0
    assert parse_turkish_amount("-31.200,00") == -31200.0


def test_extract_transaction_line() -> None:
    row = _extract_transaction_from_line(
        "28/04/2026 MOKA UNITED/YEMEKSEPETI ISTANBUL TR 329,99 0,03",
        page_number=3,
    )
    assert row is not None
    assert row["Sayfa"] == 3
    assert row["Tutar"] == 329.99
    assert row["Islem_Tipi"] == "Harcama"


def test_categories() -> None:
    assert categorize_transaction("MOKA UNITED/YEMEKSEPETI") == "Yemek"
    assert categorize_transaction("PARAM/BELBIM ELEKTRONIK") == "Ulaşım"
    assert categorize_transaction("GOOGLE YOUTUBE PREMIUM") == "Abonelik / Dijital"


def test_transaction_types() -> None:
    assert classify_transaction_type("HESAPTAN AKTARIM", -1000) == "Ödeme"
    assert classify_transaction_type("TRENDYOL IADE", -200) == "İade / İptal"
    assert classify_transaction_type("FAIZ TUTARI", 250) == "Faiz / Masraf"
