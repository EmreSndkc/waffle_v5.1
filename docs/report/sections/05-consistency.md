## 5 Consistency

Tutarlılık kuralı tektir: snapshot her zaman kaynak tablolardan hesaplanabilecek değere eşit olmalıdır. Bunu üç mekanizma sağlar.

### 1. Değişiklik ve yeniden hesaplama aynı transaction'dadır

Tetikleyiciler kaydın yazıldığı transaction içinde çalışır. `ATOMIC_REQUESTS` açık olduğu için bir HTTP isteğindeki not kaydı ile PO güncellemesi ya birlikte yazılır ya hiç yazılmaz. İstek dışındaki kullanım için servis aynı garantiyi kendisi verir:

```python
@classmethod
@transaction.atomic
def save_grade(cls, student, assessment, score):
    grade = (StudentGrade.objects.select_for_update()
             .filter(student=student, assessment=assessment).first()
             ) or StudentGrade(student=student, assessment=assessment)
    grade.score = Decimal(str(score))
    grade.full_clean()     # 0–100 dışı not burada reddedilir
    grade.save()           # post_save sinyali PO'ları yeniden hesaplar
    return grade
```

### 2. Aynı öğrenci için hesaplamalar sıraya girer

PostgreSQL'in varsayılan izolasyon düzeyi READ COMMITTED'dır. Bu düzeyde aynı öğrencinin iki notu aynı anda kaydedilirse, iki hesaplama da diğerinin notunu görmeden snapshot yazabilir. Bunu önlemek için hesaplama önce öğrenci satırını kilitler:

```python
@classmethod
@transaction.atomic
def calculate_student_profile(cls, student):
    locked = User.objects.select_for_update().filter(pk=student.pk).first()
    ...
```

İkinci hesaplama birincinin commit'ini bekler ve güncel notları okur. Toplu hesaplamada öğrenciler `pk` sırasıyla kilitlenir; böylece iki toplu işlem birbirini kilitleyemez (deadlock). SQLite'ta `select_for_update` etkisizdir; orada yazmalar zaten tek tek yapılır.

### 3. Veritabanı kısıtları

Uygulama katmanını atlayan yazmalar (toplu yükleme, elle SQL) da kurallara uyar: unique kısıtlar aynı öğrenciye aynı değerlendirmeden iki not yazılmasını, `CHECK` kısıtları 0–100 dışı notu ve 1–5 dışı ağırlığı engeller.

### Hangi değişiklik kimi yeniden hesaplatır

| Değişen kayıt | Yeniden hesaplanan öğrenciler |
|---|---|
| `StudentGrade` (ekleme, güncelleme, silme) | Notun sahibi |
| `Assessment_LO_Mapping` | O değerlendirmeden notu olan öğrenciler |
| `LO_PO_Mapping` | O LO'yu besleyen değerlendirmelerden notu olan öğrenciler |

### Testler

`python manage.py test` 15 testi SQLite ve PostgreSQL 18 üzerinde geçirir: hocanın örneği (LO1 86.0, LO2 82.9, PO1 85.0, PO2 82.9), verisi olmayan PO'nun NULL olması, not/eşleme/ağırlık değişince ve silinince yeniden hesaplama, geçersiz notun reddedilip snapshot'ın değişmemesi.

### Bilinen eksikler

- `Assessment.max_score` hesaplamaya katılmıyor; notlar 0–100 kabul ediliyor.
- `QuerySet.update()` ve `bulk_create()` sinyal üretmez; toplu not yükleme geldiğinde servis açıkça çağrılacak.
- Eşzamanlılık testi (iki bağlantıyla aynı anda yazma) henüz yok; kilit davranışı kod incelemesiyle doğrulandı.
