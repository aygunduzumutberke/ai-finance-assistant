# AI Finans Asistanı V2

PDF kredi kartı ekstrelerinden işlem verilerini çıkaran; harcamaları kategorilere ayıran, bütçe takibi yapan, düzenli ödeme ve olağandışı işlem adaylarını tespit eden, finansal sağlık puanı üreten ve Excel dashboard raporu oluşturan Streamlit uygulaması.

> Proje açıklanabilir ve kural tabanlı bir analiz yaklaşımı kullanır. Sonuçlar finansal danışmanlık değildir.

## V2 ile gelen özellikler

- PDF ekstre yükleme ve tek tuşla analiz
- Tamamen kurgusal verili **Demo Modu**
- Harcama, ödeme, iade, puan ve faiz/masraf ayrımı
- Merchant normalizasyonu ve tekrar okunan satırların temizlenmesi
- Genişletilmiş kategori sözlüğü
- Aylık ve kategori bazlı harcama analizi
- Önceki aya göre harcama değişimi
- Kullanıcı tarafından değiştirilebilen kategori bütçeleri
- Bütçe aşımı ve bütçeye yaklaşma uyarıları
- Düzenli ödeme / abonelik adayı tespiti
- Robust istatistiklerle olağandışı yüksek işlem tespiti
- Açıklanabilir **Finansal Sağlık Puanı (0-100)**
- Tahmini tasarruf potansiyeli
- Merchant bazlı kategori düzeltme ve yeniden analiz
- Plotly tabanlı web dashboard
- Geliştirilmiş Excel dashboard ve detay sayfaları
- GitHub Actions ile Python 3.10, 3.11 ve 3.12 otomatik testleri

## Uygulama akışı

```text
PDF ekstre veya Demo Modu
           ↓
İşlemleri çıkar / normalize et / tekrarları temizle
           ↓
İşlem türü ve kategori sınıflandırması
           ↓
Aylık analiz + bütçe takibi + önceki ay karşılaştırması
           ↓
Düzenli ödeme + anomali + davranış tespitleri
           ↓
Finansal sağlık puanı + tasarruf potansiyeli
           ↓
Streamlit dashboard + Excel V2 raporu
```

## Ekran bölümleri

| Bölüm | İçerik |
|---|---|
| Dashboard | Ana metrikler, kategori dağılımı, aylık trend ve davranış tespitleri |
| Bütçe | Kategori bütçesi, gerçekleşen harcama, kalan tutar ve kullanım oranı |
| Düzenli Ödemeler | Abonelik ve tekrarlayan ödeme adayları |
| Anomaliler | Aylık tipik işlem seviyesinin üzerindeki işlemler |
| İşlemler | Kategori filtreli detay işlem tablosu |
| Kategori Düzeltme | Merchant kategorilerini düzenleyip analizi yeniden çalıştırma |
| Finans Yorumu | Açıklanabilir aylık değerlendirme |
| Excel Raporu | Tüm analizleri ve Excel içi dashboard'u indirme |

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

Bağımlılıkları yükleyin:

```bash
python -m pip install -r requirements.txt
```

Uygulamayı çalıştırın:

```bash
python -m streamlit run app.py
```

Tarayıcıda genellikle `http://localhost:8501` açılır.

## Testler

```bash
python -m pytest -q
```

GitHub Actions her push ve pull request'te testleri otomatik çalıştırır.

## Proje yapısı

```text
ai-finance-assistant/
├── app.py                         # Streamlit arayüzü
├── finance_core.py                # Eski importlar için uyumluluk katmanı
├── src/ai_finance_assistant/
│   ├── __init__.py
│   ├── models.py                  # Veri modelleri ve özel hatalar
│   ├── parsing.py                 # PDF okuma, merchant ve kategori işlemleri
│   ├── analytics.py               # Bütçe, anomali, tekrar ve puan analizleri
│   ├── pipeline.py                # Uçtan uca analiz akışı
│   ├── reporting.py               # Excel raporu ve dashboard
│   └── demo.py                    # Kurgusal demo verisi
├── tests/
│   ├── test_core.py
│   └── test_v2_analytics.py
├── .github/workflows/tests.yml
├── requirements.txt
├── CHANGELOG.md
└── LICENSE
```

## Analiz yaklaşımı

### Kategori çıkarımı

İşlem açıklaması normalize edilir, merchant adı sadeleştirilir ve açıklanabilir anahtar kelime kuralları uygulanır. Kullanıcı, web arayüzünde yanlış kategorileri merchant bazında düzeltebilir.

### Düzenli ödeme tespiti

Aynı merchant'ın birden fazla ayda benzer tutarlarda görünmesi değerlendirilir. Tutar değişkenliği yüksek olan işlemler düzenli ödeme olarak işaretlenmez.

### Anomali tespiti

Son aydaki işlemler için medyan, MAD ve IQR tabanlı robust eşikler kullanılır. Böylece tek bir yüksek işlem ortalamayı bozsa bile daha dayanıklı sonuç üretilir.

### Finansal sağlık puanı

Puan; bütçe aşımları, risk seviyeleri ve önceki aya göre değişim üzerinden 0-100 aralığında hesaplanır. Amaç kullanıcıya açıklanabilir bir özet sinyal vermektir.

### Tasarruf potansiyeli

İsteğe bağlı kategoriler, bütçe aşımları ve düzenli ödeme adayları üzerinde muhafazakâr oranlarla tahmini bir fırsat tutarı hesaplanır.

## Excel raporu

Oluşturulan `.xlsx` dosyası şunları içerir:

- Dashboard
- Genel özet
- Ham PDF işlemleri
- Analiz verisi
- İşlem tipi özeti
- Kategori özeti
- Aylık özet
- Bütçe takibi
- Düzenli ödemeler
- Anomaliler
- Harcama tespitleri
- En yüksek 15 işlem
- Finans yorumu

## Gizlilik

- Gerçek ekstre veya kişisel finans verisi repoya dahil edilmez.
- PDF, uygulama sırasında geçici klasörde işlenir.
- `.gitignore` PDF, Excel ve yerel çıktı klasörlerini dışarıda bırakır.
- Demo modu tamamen kurgusal veri kullanır.
- Uygulama üçüncü taraf bir ortama deploy edilirse o platformun veri politikaları ayrıca değerlendirilmelidir.

## Sınırlamalar

- Şu an yalnızca metin katmanı bulunan PDF'ler desteklenir.
- Taranmış görüntü PDF'ler için OCR henüz yoktur.
- Farklı banka formatları ayrı parser uyarlaması gerektirebilir.
- Düzenli ödeme ve anomali sonuçları aday tespitidir; kullanıcı doğrulaması gerekir.

## Teknolojiler

Python · Streamlit · pandas · NumPy · pdfplumber · Plotly · openpyxl · pytest · GitHub Actions

## Yol haritası

- Çoklu banka parser mimarisi
- OCR desteği
- Kullanıcı kategori kurallarını yerel dosyada saklama
- CSV / Excel ekstre desteği
- Harcama hedefleri ve bildirimler
- Opsiyonel yerel makine öğrenmesi kategori modeli

## CV için kısa açıklama

> Developed a privacy-conscious Streamlit personal finance analytics application that extracts transactions from PDF credit card statements, normalizes merchants, tracks category budgets, detects recurring payments and anomalous spending, calculates an explainable financial health score, and exports an Excel dashboard report.

## Lisans

MIT
