## 3 Data Model

Şema on tablodan oluşur. Dokuz kaynak tablo 3NF'tedir: her not ve her ağırlık tek bir yerde durur. Onuncu tablo `StudentPOSnapshot` türetilmiş veridir (öğrenci × PO başına tek satır) ve okuma yükünü hesaplamadan ayırmak için bilinçli olarak denormalize edilmiştir. Kaynak tablolar OLTP tarafıdır; snapshot, öğrenci ve PO boyutlarına bağlı bir olgu tablosu gibi davranır.

### Bu sprintte yapılan düzeltmeler

| Düzeltme | Neden |
|---|---|
| `Enrollment` (öğrenci ↔ ders) tablosu eklendi | Hangi öğrencinin hangi derste olduğu tutulmuyordu |
| `LO_PO_Mapping.weight` tam sayı oldu, 1–5 `CHECK` kısıtı eklendi | Hocanın tanımı 1–5; ondalık alan 0.01'i kabul ediyordu |
| `StudentPOSnapshot.score` NULL olabilir | Verisi olmayan PO'ya 0.00 yazmak öğrenciyi haksız yere düşük gösteriyordu |
| Roller dörde çıktı: `ADMIN`, `DEPT_HEAD`, `INSTRUCTOR`, `STUDENT` | Bölüm Başkanı ile sistem yöneticisi aynı roldeydi |
| Unique kısıtlar adlandırıldı; not 0–100 ve ağırlık > 0 için `CHECK` eklendi | Kural uygulama katmanını atlayan yazmalarda da geçerli olsun |
| Her eşleme tablosuna ters yönlü bileşik index eklendi | Unique index yalnızca bir yönü karşılıyordu |

### Kısıtlar ve index'ler

| Tablo | Unique | Check | Ek index |
|---|---|---|---|
| `User` | `username`, `student_number` | — | `(role)` |
| `ProgramOutcome` | `code` | — | — |
| `Course` | `code` | — | — |
| `Enrollment` | `(student, course)` | — | `(course, student)` |
| `LearningOutcome` | `(course, code)` | — | — |
| `LO_PO_Mapping` | `(learning_outcome, program_outcome)` | `weight` 1–5 | `(program_outcome, learning_outcome)` |
| `Assessment` | `(course, name)` | — | — |
| `Assessment_LO_Mapping` | `(assessment, learning_outcome)` | `weight > 0` | `(learning_outcome, assessment)` |
| `StudentGrade` | `(student, assessment)` | `score` 0–100 | `(assessment, student)` |
| `StudentPOSnapshot` | `(student, program_outcome)` | — | `(program_outcome, score)` |

### Tablo boyutları (demo verisi, PostgreSQL 18)

`seed_demo` sonrası `pg_relation_size`, `pg_indexes_size` ve `pg_total_relation_size` ile ölçülmüştür.

| Tablo | Satır | Sütun | Veri (B) | Index (B) | Toplam (B) |
|---|---|---|---|---|---|
| `outcomes_user` | 11 | 13 | 8 192 | 98 304 | 114 688 |
| `outcomes_programoutcome` | 11 | 4 | 8 192 | 49 152 | 65 536 |
| `outcomes_course` | 3 | 5 | 8 192 | 65 536 | 73 728 |
| `outcomes_enrollment` | 16 | 4 | 8 192 | 81 920 | 90 112 |
| `outcomes_learningoutcome` | 7 | 4 | 8 192 | 49 152 | 65 536 |
| `outcomes_lo_po_mapping` | 11 | 4 | 8 192 | 81 920 | 90 112 |
| `outcomes_assessment` | 7 | 4 | 8 192 | 49 152 | 57 344 |
| `outcomes_assessment_lo_mapping` | 13 | 4 | 8 192 | 81 920 | 90 112 |
| `outcomes_studentgrade` | 37 | 5 | 8 192 | 81 920 | 90 112 |
| `outcomes_studentposnapshot` | 66 | 5 | 32 768 | 81 920 | 139 264 |

Bu hacimde her tablo tek bir 8 KB sayfaya sığar; boyutu index'ler belirler. Tek istisna snapshot tablosudur: 66 satır için dört sayfa kullanır, çünkü seed sırasında her not kaydı aynı satırları yeniden yazmış ve PostgreSQL eski satır sürümlerini (MVCC) henüz temizlememiştir. Gerçekçi hacimli ölçüm (500 öğrenci, 40 ders) final raporunda yapılacaktır.

![Şekil 4 — ER diyagramı](../diagrams/er.png)
