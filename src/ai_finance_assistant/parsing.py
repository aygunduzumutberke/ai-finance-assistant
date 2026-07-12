from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import Any

import pandas as pd
import pdfplumber

from .models import StatementParseError

TRANSACTION_COLUMNS = [
    "Sayfa",
    "Tarih",
    "Açıklama",
    "Merchant",
    "Tutar",
    "Ek_Bilgi",
    "Islem_Tipi",
]

CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Faiz / Masraf", ("FAIZ", "MASRAF", "KOMISYON", "BSMV", "KKDF")),
    ("Nakit Çekim", ("NAKITAVANS", "ATM", "NAKITCEKIM")),
    ("Ulaşım", ("BELBIM", "UBER", "MARMARAY", "AKARYAKIT", "SHELL", "OPET", "METRO", "TAKSI", "MARTI")),
    ("Market", ("GETIRPERAK", "MIGROS", "CARREFOURSA", "MARKET", "BIM", "A101", "SOKMARKET", "ISTEGELSIN")),
    ("Yemek", ("YEMEKSEPETI", "TRENDYOLYEMEK", "GETIRYEMEK", "POPEYES", "TAVUKDUNYASI", "LOKANTA", "RESTORAN", "CATERING", "GREENSALADS", "PEHLIVAN", "BURGERKING", "MCDONALDS", "KFC")),
    ("Kafe", ("KAFE", "CAFE", "COFFEE", "ESPRESSO", "MADO", "STARBUCKS", "KAHVE", "MOC")),
    ("Abonelik / Dijital", ("APPLECOM", "YOUTUBE", "SPOTIFY", "NETFLIX", "GOOGLE", "DISNEY", "BLUTV", "EXXEN", "ICLOUD")),
    ("E-Ticaret", ("TRENDYOLCOM", "HEPSIBURADA", "AMAZON", "N11COM", "PAZARAMA")),
    ("Giyim", ("ZARA", "LCWAIKIKI", "BERSHKA", "YILDIZSTORE", "PULLANDBEAR", "MAVI", "DEFACTO", "KOTON")),
    ("Kişisel Bakım", ("GRATIS", "WATSONS", "ROSSMANN", "SEPHORA", "KUAFOR")),
    ("Sağlık", ("ECZANE", "HASTANE", "MEDIKAL", "DOKTOR", "DENTAL")),
    ("Eğlence", ("BILETIX", "PASSO", "SINEMA", "CINEMAXIMUM", "KONSER")),
    ("Tütün", ("TOBACCO", "TEKEL")),
]


def normalize_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    return "".join(char for char in text if not unicodedata.combining(char)).upper().strip()


def compact_text(value: Any) -> str:
    return re.sub(r"[\s/.\-_*]+", "", normalize_text(value))


def parse_turkish_amount(value: Any) -> float | None:
    if pd.isna(value):
        return None
    text = str(value).strip().replace("₺", "").replace("TL", "").replace(" ", "")
    text = text.replace(".", "").replace(",", ".")
    try:
        return float(text)
    except ValueError:
        return None


def normalize_merchant(description: str) -> str:
    text = normalize_text(description)
    text = re.sub(r"\b(TR|TURKIYE|ISTANBUL|ANKARA|IZMIR|POS|SANALPOS)\b", " ", text)
    text = re.sub(r"\d{4,}", " ", text)
    text = re.sub(r"[^A-Z0-9ÇĞİÖŞÜ ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:60] or "BILINMEYEN"


def classify_transaction_type(description: str, amount: float) -> str:
    normalized = normalize_text(description)
    compact = compact_text(description)
    if "HESAPTANAKTARIM" in compact or "ODEME" in normalized:
        return "Ödeme"
    if "MAXIPUAN" in compact or "PUANILAVE" in compact:
        return "Puan İşlemi"
    if amount < 0:
        return "İade / İptal"
    if any(keyword in normalized for keyword in ("FAIZ", "MASRAF", "KOMISYON", "BSMV", "KKDF")):
        return "Faiz / Masraf"
    return "Harcama"


def categorize_transaction(description: str) -> str:
    normalized = normalize_text(description)
    compact = compact_text(description)
    for category, keywords in CATEGORY_RULES:
        if any(keyword in compact or keyword in normalized for keyword in keywords):
            return category
    return "Diğer"


def extract_transaction_from_line(line: str, page_number: int) -> dict[str, Any] | None:
    date_match = re.match(r"^(\d{2}/\d{2}/\d{4})\s+(.+)$", line)
    if not date_match:
        return None

    date_text, remainder = date_match.group(1), date_match.group(2)
    amount_pattern = r"(?<![\d.,])-?(?:\d{1,3}(?:\.\d{3})+|\d+),\d{2}(?![\d.,])"
    amount_match = re.search(amount_pattern, remainder)
    if not amount_match:
        return None

    description = remainder[: amount_match.start()].strip()
    amount = parse_turkish_amount(amount_match.group())
    if not description or amount is None:
        return None

    return {
        "Sayfa": page_number,
        "Tarih": date_text,
        "Açıklama": description,
        "Merchant": normalize_merchant(description),
        "Tutar": amount,
        "Ek_Bilgi": remainder[amount_match.end() :].strip(),
        "Islem_Tipi": classify_transaction_type(description, amount),
    }


def read_credit_card_statement(pdf_path: str | os.PathLike[str]) -> pd.DataFrame:
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"Dosya bulunamadı: {path}")

    rows: list[dict[str, Any]] = []
    try:
        with pdfplumber.open(path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
                for raw_line in text.splitlines():
                    transaction = extract_transaction_from_line(" ".join(raw_line.split()), page_number)
                    if transaction:
                        rows.append(transaction)
    except Exception as exc:
        raise StatementParseError(f"PDF okunamadı: {exc}") from exc

    frame = pd.DataFrame(rows, columns=TRANSACTION_COLUMNS)
    if frame.empty:
        raise StatementParseError(
            "PDF içerisinden işlem satırı çıkarılamadı. Dosya taranmış olabilir "
            "veya ekstre formatı henüz desteklenmiyor olabilir."
        )

    frame["Tarih"] = pd.to_datetime(frame["Tarih"], format="%d/%m/%Y", errors="coerce")
    frame = frame.dropna(subset=["Tarih"]).copy()
    frame["Tutar"] = pd.to_numeric(frame["Tutar"], errors="coerce")
    frame = frame.dropna(subset=["Tutar"])

    # Aynı sayfada aynı tarih/açıklama/tutar ile tekrar okunan satırları temizle.
    frame = frame.drop_duplicates(subset=["Sayfa", "Tarih", "Açıklama", "Tutar"])
    frame = frame.sort_values(["Tarih", "Sayfa"]).reset_index(drop=True)

    if frame.empty:
        raise StatementParseError("İşlem tarihleri veya tutarları okunamadı.")
    return frame
