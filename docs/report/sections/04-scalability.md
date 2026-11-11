## 4 Scalability & Fault Tolerance

Bu bölüm bir plandır. Yapılanlar ve yapılacaklar ayrı gösterilmiştir.

### Yük profili

Sistem okuma ağırlıklıdır: not dönemde birkaç kez yazılır, PO profili ise her panel açılışında okunur. Tasarımın ana fikri, pahalı hesabı yazma anına taşıyıp okumayı tek tablodan yapmaktır.

### Yapılanlar

| Teknik | Nerede | Ne kazandırır |
|---|---|---|
| Ön hesaplama | `StudentPOSnapshot` | PO profili üç tablolu join ve toplama yerine tek index'li okumadır |
| Artımlı yeniden hesaplama | `outcomes/signals.py` | Bir değişiklik yalnızca etkilenen öğrencileri yeniden hesaplatır |
| Bileşik B-tree index'ler | Tüm eşleme, not ve snapshot tabloları | Her iki sorgu yönü de (öğrenci → not, değerlendirme → not) index'ten karşılanır |
| Yeniden üretilebilir snapshot | `POCalculatorService.recalculate_students` | Snapshot bozulur ya da silinirse kaynak tablolardan yeniden kurulur |
| Ortamdan bağımsız yapılandırma | `config/settings.py` | Aynı kod SQLite ile dizüstünde, PostgreSQL ile sunucuda çalışır |

### Planlananlar

| Teknik | Ne zaman gerekir | Not |
|---|---|---|
| Redis cache (ders × PO ortalamaları) | Bölüm başkanı paneli geldiğinde | Ayar hazır; cache'lenecek sorgu henüz yok |
| PostgreSQL materialized view (ders × PO) | Isı haritası raporu geldiğinde | Dönem içinde periyodik `REFRESH` |
| Arka plan kuyruğu | Bir ağırlık değişikliği yüzlerce öğrenciyi etkilediğinde | Bugün yeniden hesaplama istek içinde, eşzamanlı çalışır |
| Günlük `pg_dump` yedeği | Canlıya çıkışta | Snapshot yedeklenmese de yeniden üretilebilir |
| Bağlantı havuzu, okuma replikası | Birden çok bölüm kullanırsa | Şimdilik `CONN_MAX_AGE = 60` yeterli |

### Beklenen hacim

500 öğrenci, 40 ders, ders başına 4 değerlendirme ve öğrenci başına dönemde 6 ders varsayımıyla tahmin:

| Tablo | Tahmini satır |
|---|---|
| `StudentGrade` | 500 × 6 × 4 = 12 000 |
| `Enrollment` | 500 × 6 = 3 000 |
| `StudentPOSnapshot` | 500 × 11 = 5 500 |
| Eşleme tabloları | birkaç yüz |

Bu hacim tek bir PostgreSQL sunucusu için küçüktür. Darboğaz veri boyutu değil, toplu yeniden hesaplamadır: çok öğrencili bir dersin LO→PO ağırlığı değişince o dersin tüm öğrencileri aynı transaction içinde yeniden hesaplanır.

### Hata durumları

| Hata | Davranış |
|---|---|
| Hesaplama sırasında istisna | Transaction geri alınır; not ve snapshot eski hâlinde kalır |
| Redis erişilemez | Cache'lenen sorgu olmadığı için bugün etkisi yok; ileride veritabanına düşülecek |
| SMTP erişilemez | E-posta gönderen özellik henüz yok |
| Snapshot tutarsızlığı şüphesi | `recalculate_students` ile tüm öğrenciler yeniden hesaplanır |
