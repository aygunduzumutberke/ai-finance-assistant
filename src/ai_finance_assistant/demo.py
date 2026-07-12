from __future__ import annotations

import random
from datetime import datetime, timedelta

import pandas as pd

from .parsing import classify_transaction_type, normalize_merchant


DEMO_MERCHANTS = [
    ("YEMEKSEPETI", 380, 0.30),
    ("STARBUCKS", 185, 0.12),
    ("MIGROS", 950, 0.18),
    ("BELBIM", 300, 0.10),
    ("TRENDYOLCOM", 1250, 0.12),
    ("ZARA", 1800, 0.06),
    ("GRATIS", 520, 0.05),
    ("ECZANE", 650, 0.04),
    ("SHELL", 1600, 0.03),
]

RECURRING = [
    ("NETFLIX", 229.99),
    ("SPOTIFY", 79.99),
    ("GOOGLE YOUTUBE PREMIUM", 79.99),
]


def create_demo_transactions(seed: int = 42) -> pd.DataFrame:
    """Create a deterministic, fictional three-month statement for demo mode."""
    rng = random.Random(seed)
    rows: list[dict] = []
    page = 1
    start_months = [datetime(2026, 3, 1), datetime(2026, 4, 1), datetime(2026, 5, 1)]

    for month_index, month_start in enumerate(start_months):
        for merchant, base_amount, weight in DEMO_MERCHANTS:
            count = max(1, round(weight * 45 + rng.randint(-2, 2)))
            for _ in range(count):
                day = rng.randint(0, 26)
                amount = max(25.0, rng.gauss(base_amount * (1 + month_index * 0.05), base_amount * 0.22))
                rows.append(
                    {
                        "Sayfa": page,
                        "Tarih": month_start + timedelta(days=day),
                        "Açıklama": merchant,
                        "Merchant": normalize_merchant(merchant),
                        "Tutar": round(amount, 2),
                        "Ek_Bilgi": "DEMO",
                        "Islem_Tipi": "Harcama",
                    }
                )
        for merchant, amount in RECURRING:
            rows.append(
                {
                    "Sayfa": page,
                    "Tarih": month_start + timedelta(days=5),
                    "Açıklama": merchant,
                    "Merchant": normalize_merchant(merchant),
                    "Tutar": amount,
                    "Ek_Bilgi": "DEMO ABONELIK",
                    "Islem_Tipi": "Harcama",
                }
            )
        page += 1

    # Son ayda anomali, faiz ve bir iade ekle.
    rows.extend(
        [
            {
                "Sayfa": 3,
                "Tarih": datetime(2026, 5, 18),
                "Açıklama": "AMAZON YUKSEK TUTARLI ALISVERIS",
                "Merchant": normalize_merchant("AMAZON YUKSEK TUTARLI ALISVERIS"),
                "Tutar": 12999.0,
                "Ek_Bilgi": "DEMO ANOMALI",
                "Islem_Tipi": "Harcama",
            },
            {
                "Sayfa": 3,
                "Tarih": datetime(2026, 5, 25),
                "Açıklama": "AKDI FAIZ TUTARI",
                "Merchant": normalize_merchant("AKDI FAIZ TUTARI"),
                "Tutar": 420.0,
                "Ek_Bilgi": "DEMO",
                "Islem_Tipi": "Faiz / Masraf",
            },
            {
                "Sayfa": 3,
                "Tarih": datetime(2026, 5, 27),
                "Açıklama": "TRENDYOLCOM IADE",
                "Merchant": normalize_merchant("TRENDYOLCOM IADE"),
                "Tutar": -480.0,
                "Ek_Bilgi": "DEMO",
                "Islem_Tipi": classify_transaction_type("TRENDYOLCOM IADE", -480.0),
            },
        ]
    )

    return pd.DataFrame(rows).sort_values("Tarih").reset_index(drop=True)
