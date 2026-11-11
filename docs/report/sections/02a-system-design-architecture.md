## 2 System Design

### 2.1 Sistem mimarisi

Sistem tek bir Django uygulama sunucusudur. Tarayıcıdan gelen istek `config/` altındaki URL ve ayarlardan geçer, `outcomes/` uygulamasında yetki kontrolünden sonra modellere ve hesaplama servisine ulaşır. Dış bileşenlerin tamamı `config/settings.py` içinde ortam değişkenleriyle seçilir; değişken tanımlı değilse yerel bir karşılığa düşer, böylece proje ek kurulum olmadan çalışır.

| Bileşen | Görevi | Ortam değişkeni | Tanımlı değilse | Bugünkü durum |
|---|---|---|---|---|
| PostgreSQL | Kalıcı veri | `POSTGRES_DB` … | SQLite | Kullanılıyor; testler PostgreSQL 18'de geçiyor |
| Redis | Rapor sorgularının cache'i | `REDIS_URL` | Süreç içi bellek | Yapılandırıldı; henüz cache'lenen sorgu yok |
| SMTP | E-posta bildirimi | `EMAIL_HOST` … | Konsola yazar | Yapılandırıldı; henüz e-posta gönderen özellik yok |
| Dosya depolama | Excel/CSV not dosyaları, syllabus PDF | `MEDIA_ROOT` | `./media` | Yapılandırıldı; yükleme ekranı henüz yok |

Veritabanı seçimi tek bir koşuldur:

```python
if os.environ.get("POSTGRES_DB"):
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["POSTGRES_DB"],
        "ATOMIC_REQUESTS": True,   # her HTTP isteği tek transaction
        ...
    }}
else:
    DATABASES = {"default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "ATOMIC_REQUESTS": True,
    }}
```

![Şekil 2 — Sistem mimarisi](../diagrams/architecture.png)
