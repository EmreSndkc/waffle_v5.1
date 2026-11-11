## 1 Introduction

Waffle 5.1, Acıbadem Üniversitesi CSE bölümü için her öğrencinin 11 Program Outcome (PO) puanını hesaplayan, Python + Django ile yazılmış bir web sistemidir. Hesap zinciri üç basamaklıdır: değerlendirme notu → (yüzdelerle) Learning Outcome (LO) → (1–5 ağırlıkla) PO. Her basamakta aynı formül kullanılır:

```
puan = Σ(ağırlık × puan) ÷ Σ ağırlık
```

### Temel özellikler (bugünkü durum)

| Özellik | Durum |
|---|---|
| Veri modeli: kullanıcı/rol, ders, kayıt, LO, PO, değerlendirme, not, eşlemeler | Çalışıyor |
| PO hesaplama servisi ve ön hesaplanmış PO profili (`StudentPOSnapshot`) | Çalışıyor |
| Not, eşleme ya da ağırlık değişince otomatik yeniden hesaplama | Çalışıyor |
| Verisi olmayan PO için 0 yerine NULL ("veri yok") | Çalışıyor |
| Django admin paneli: tüm modeller, liste/filtre/arama | Çalışıyor |
| Demo verisi: `python manage.py seed_demo` (11 PO, 3 ders, her rol için kullanıcı) | Çalışıyor |
| Rol bazlı ekranlar, öğrenci paneli, toplu not yükleme, raporlar | Sonraki sprintler |

### Kabul testi (hocanın örneği)

Midterm 90, Project 80 alan öğrenci için sistem LO1 = 86.0, LO2 = 82.9, PO1 = 85.0, PO2 = 82.9 üretir. Bu örnek hem birim testidir hem de demo verisindeki `elif` kullanıcısıdır.

### Roller

| Rol | Kod | Girer | Görür |
|---|---|---|---|
| Sistem Yöneticisi | `ADMIN` | Kullanıcılar, roller | Her şey |
| Bölüm Başkanı | `DEPT_HEAD` | PO'lar, dersler, hoca ataması, öğrenci kaydı | Tüm dersler ve tüm öğrencilerin PO puanları |
| Öğretim Üyesi | `INSTRUCTOR` | LO'lar, değerlendirmeler, yüzdeler, LO→PO ağırlıkları, notlar | Dersler, notlar, PO puanları |
| Öğrenci | `STUDENT` | — | Kendi notları ve PO profili |

Kural: kurumsal yapıyı (PO, ders) bölüm, ders içeriğini (LO, ağırlık, not) hoca girer; öğrenci yalnızca kendi verisini görür. Bugün Bölüm Başkanı ve Öğretim Üyesi yetkileri Django admin'de iki yetki grubu olarak tanımlıdır. Yetki model düzeyindedir; "hoca yalnızca kendi dersini görür" kontrolü ve öğrenci paneli henüz yoktur.

![Şekil 1 — Roller: kim neyi girer, kim neyi görür](../diagrams/roles.png)
