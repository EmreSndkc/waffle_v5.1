# Sistem mimarisi

![Sistem mimarisi](architecture.png)

Kaynak: `architecture.svg` (vektör), `architecture.png` (rapor ve slaytlar için).

```mermaid
flowchart LR
    B["Tarayıcı<br/>Admin · Bölüm Başkanı · Öğretim Üyesi · Öğrenci"]
    subgraph D["Django uygulama sunucusu"]
        C["config/<br/>settings · urls"]
        subgraph O["outcomes/ (app)"]
            V["Admin paneli / View'lar"]
            S["POCalculatorService"]
            M["Modeller (ORM)"]
            V --> S --> M
        end
    end
    PG[("PostgreSQL<br/>OLTP tabloları + StudentPOSnapshot")]
    R[("Redis cache")]
    E["SMTP e-posta"]
    F[("Dosya depolama<br/>Excel/CSV · syllabus PDF")]
    B -- "HTTP(S)" --> D
    D -- "SQL (ORM)" --> PG
    D -- "get / set" --> R
    D -- "SMTP" --> E
    D -- "oku / yaz" --> F
```

## Bileşenler

| Bileşen | Görevi | Ayar (`config/settings.py`) | Tanımlı değilse |
|---|---|---|---|
| Tarayıcı | Dört rolün arayüzü (şimdilik Django admin) | — | — |
| Django | İstekleri karşılar, yetki kontrolü yapar, PO hesaplar | `INSTALLED_APPS`, `AUTH_USER_MODEL` | — |
| PostgreSQL | Kalıcı veri: normalize tablolar + ön hesaplanmış `StudentPOSnapshot` | `POSTGRES_*` | SQLite |
| Redis | Sık okunan rapor/ortalama sorgularının cache'i | `REDIS_URL` | Süreç içi bellek |
| SMTP | E-posta bildirimleri | `EMAIL_HOST` … | Konsola yazar |
| Dosya depolama | Toplu not Excel/CSV dosyaları, syllabus PDF'leri | `MEDIA_ROOT` | `./media` |
