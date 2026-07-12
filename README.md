# AI Finans Asistanı

PDF kredi kartı ekstrelerinden işlem verilerini çıkaran, harcamaları kategorilere ayıran, dikkat edilmesi gereken harcama davranışlarını tespit eden ve Excel dashboard raporu üreten Streamlit uygulaması.

## Özellikler

- Metin tabanlı PDF kredi kartı ekstresi okuma
- Harcama, ödeme, iade, puan ve faiz/masraf ayrımı
- İşlem açıklamasından kategori çıkarımı
- Aylık ve kategori bazlı harcama analizi
- Kural tabanlı harcama davranışı tespitleri
- Web dashboard üzerinde Plotly grafikleri
- Dashboard içeren Excel raporu
- Geçici dosya kullanımı ile gizlilik odaklı çalışma
- Desteklenmeyen PDF formatları için anlaşılır hata mesajları

## Demo akışı

```text
PDF ekstre yükle
        ↓
İşlemleri çıkar ve sınıflandır
        ↓
Kategori / aylık analiz oluştur
        ↓
Harcama davranışı tespitleri üret
        ↓
Streamlit dashboard göster
        ↓
Excel dashboard raporunu indir
```

## Kurulum

Python 3.11 önerilir.

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

Paketleri yükleyin:

```bash
python -m pip install -r requirements.txt
```

Uygulamayı çalıştırın:

```bash
python -m streamlit run app.py
```

Tarayıcıda genellikle `http://localhost:8501` adresi açılır.

## Testler

```bash
python -m pytest
```

## Proje yapısı

```text
ai-finance-assistant/
├── app.py
├── finance_core.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── .streamlit/
│   └── config.toml
├── sample_data/
│   └── README.md
└── tests/
    └── test_core.py
```

## Analiz motoru hakkında

Kategori çıkarımı ve risk tespitleri şu an **şeffaf, kural tabanlı** çalışır. Bu tercih MVP aşamasında:

- Sonuçların açıklanabilir olmasını,
- Yeni merchant kurallarının kolay eklenmesini,
- Model/API maliyeti olmadan yerel çalışmayı

sağlar.

Gelecek sürümlerde merchant normalizasyonu, öğrenen kategori modeli, OCR ve çoklu banka formatı desteği eklenebilir.

## Gizlilik

- Gerçek ekstre veya kişisel finans verisi repoya dahil edilmez.
- Uygulama yüklenen PDF'i geçici klasörde işler.
- `.gitignore` dosyası PDF, Excel raporu, yükleme ve çıktı klasörlerini dışarıda bırakır.
- Streamlit Cloud gibi üçüncü taraf ortamlara yüklenen verilerin platform politikaları ayrıca değerlendirilmelidir.

## Sınırlamalar

- Yalnızca metin katmanı bulunan PDF'ler desteklenir.
- OCR bulunmadığı için taranmış görüntü PDF'ler okunamaz.
- Bankaların ekstre formatları farklı olabilir; yeni formatlar için parser uyarlaması gerekebilir.
- Üretilen yorum finansal danışmanlık değildir.

## Teknolojiler

- Python
- Streamlit
- pandas
- pdfplumber
- Plotly
- openpyxl

## CV için kısa açıklama

> Developed a Streamlit-based personal finance analytics application that extracts transactions from PDF credit card statements, classifies spending categories, detects risky spending patterns, generates explainable financial insights, and exports an Excel dashboard report.

## Lisans

MIT
