# Changelog

Bu projedeki önemli değişiklikler bu dosyada belgelenir.

## [2.0.0] - 2026-07-13

### Eklendi

- Modüler `src/ai_finance_assistant` paket yapısı
- Kurgusal verili Demo Modu
- Merchant normalizasyonu
- Tekrarlanan PDF satırlarını temizleme
- Genişletilmiş kategori sözlüğü
- Kategori bazlı aylık bütçe takibi
- Önceki aya göre harcama değişimi
- Düzenli ödeme ve abonelik adayı tespiti
- MAD ve IQR tabanlı anomali tespiti
- Finansal sağlık puanı
- Tahmini tasarruf potansiyeli
- Merchant bazlı kategori düzeltme ve yeniden analiz
- Geliştirilmiş Streamlit dashboard
- Bütçe, düzenli ödeme ve anomali sayfaları içeren Excel V2 raporu
- Python 3.10, 3.11 ve 3.12 için GitHub Actions test akışı
- V2 analizlerini kapsayan yeni testler

### Değiştirildi

- `finance_core.py`, eski importları koruyan uyumluluk katmanına dönüştürüldü.
- README, V2 mimarisi ve özellikleriyle yeniden yazıldı.
- NumPy açık bağımlılık olarak eklendi.

## [1.0.0] - 2026-07-13

### Eklendi

- PDF kredi kartı ekstresi okuma
- İşlem türü ve kategori sınıflandırması
- Kural tabanlı harcama davranışı tespitleri
- Streamlit dashboard
- Excel raporu ve dashboard
- Temel otomatik testler
