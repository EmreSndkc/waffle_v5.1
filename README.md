# Waffle 5.1 — PO Yönetim Sistemi

Acıbadem Üniversitesi CSE 311 (Software) & CSE 321 (Data Systems) ortak dönem projesi.
Her öğrencinin 11 Program Outcome (PO) puanını hesaplayan Django web sistemi.

## Hesaplama

Değerlendirme notu → (yüzdelerle) Learning Outcome → (1–5 ağırlıkla) Program Outcome.
Her adımda aynı formül:

```
puan = Σ(ağırlık × puan) ÷ Σ ağırlık
```

Kabul testi (hocanın örneği): Midterm 90, Project 80 → LO1 = 86.0, LO2 = 82.9 → PO1 = 85.0, PO2 = 82.9.

## Proje yapısı

```
config/      Django projesi (settings, urls, wsgi/asgi)
outcomes/    Uygulama: modeller (models.py) ve PO hesaplama servisi (services.py)
docs/        Diyagramlar, rapor ve slaytlar
manage.py
```

## Kurulum

Gereksinim: Python 3.9+ (PostgreSQL ve Redis isteğe bağlı).

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Çalıştırma

Hiçbir ayar yapmadan SQLite ile çalışır:

```bash
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Yönetim paneli: http://127.0.0.1:8000/admin/

### PostgreSQL ile

`POSTGRES_DB` ortam değişkeni tanımlıysa PostgreSQL, değilse SQLite kullanılır.

```bash
createdb waffle
cp .env.example .env        # değerleri doldurun
set -a; source .env; set +a
python manage.py migrate
```

### Ortam değişkenleri

| Değişken | Tanımlı değilse | Açıklama |
|---|---|---|
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT` | SQLite (`db.sqlite3`) | Veritabanı |
| `REDIS_URL` | Süreç içi bellek cache'i | Cache |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | E-postalar konsola yazılır | SMTP |
| `MEDIA_ROOT` | `./media` | Yüklenen Excel/CSV ve syllabus PDF dosyaları |
| `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` | Geliştirme varsayılanları | Güvenlik |

## Demo verisi

```bash
python manage.py seed_demo
```

11 PO, üç ders (CSE 311, CSE 321, MAT 241), LO'lar, değerlendirmeler, eşlemeler ve her rol için demo kullanıcı yükler. Komut tekrar çalıştırılabilir; kopya kayıt üretmez.

| Rol | Kullanıcı adı | Admin paneline girer mi |
|---|---|---|
| Sistem Yöneticisi | `admin` | Evet (tam yetki) |
| Bölüm Başkanı | `baskan` | Evet (PO, ders, kayıt) |
| Öğretim Üyesi | `hoca.yazilim`, `hoca.veri`, `hoca.mat` | Evet (LO, değerlendirme, eşleme, not) |
| Öğrenci | `elif`, `can`, `zeynep`, `mert`, `selin`, `emir` | Hayır |

Parola: `outcomes/management/commands/seed_demo.py` içindeki `DEMO_PASSWORD` (ya da `--password` ile verdiğiniz değer).

`elif` hocanın örneğindeki öğrencidir (Midterm 90, Project 80): PO1 = 84.95 ≈ 85.0, PO2 = 82.86 ≈ 82.9, diğer PO'lar NULL (veri yok).

## Testler

```bash
python manage.py test
```

## Git düzeni

`main` (demo edilebilir) ← `develop` ← `feature/<kısa-ad>`. Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`).

## Ekip — Waffle 5.1 fast (high)

| Üye | Kod | Diyagram |
|---|---|---|
| EmreSndkc | Django iskeleti + ayarlar | Sistem mimarisi |
| brkznqr | Model düzeltmeleri + migration'lar | ER diyagramı |
| eminozkanca | Hesaplama servisi + otomatik yeniden hesaplama + testler | Class diyagramı |
| Berkegn | Seed verisi + Django admin paneli | Kullanıcı/rol akış şeması |
