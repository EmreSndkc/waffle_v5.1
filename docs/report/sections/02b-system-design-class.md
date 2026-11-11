### 2.2 Class diyagramı

Kod üç parçadır: modeller (`outcomes/models.py`), hesaplama servisi (`outcomes/services.py`) ve tetikleyiciler (`outcomes/signals.py`).

| Sınıf | Sorumluluğu |
|---|---|
| `User`, `Course`, `Enrollment`, `LearningOutcome`, `ProgramOutcome` | Kurumsal yapı: kim, hangi ders, hangi çıktı |
| `Assessment`, `StudentGrade` | Değerlendirmeler ve ham notlar |
| `Assessment_LO_Mapping`, `LO_PO_Mapping` | Ağırlıklar: değerlendirme → LO (katsayı), LO → PO (1–5) |
| `StudentPOSnapshot` | Ön hesaplanmış PO profili; yalnızca servis yazar |
| `POCalculatorService` | Not → LO → PO hesabı, snapshot yazımı, etkilenen öğrencilerin bulunması |
| `signals` | Not, eşleme ya da ağırlık değişince servisi çağırır |

Formül tek bir fonksiyondadır ve iki adımda da aynı fonksiyon kullanılır:

```python
def weighted_average(pairs):
    weighted_sum, total_weight = Decimal('0'), Decimal('0')
    for weight, score in pairs:
        weighted_sum += Decimal(weight) * Decimal(score)
        total_weight += Decimal(weight)
    if total_weight == 0:
        return None            # veri yok: 0 değil
    return weighted_sum / total_weight
```

### Hesaplama örneği

| Adım | Hesap | Sonuç |
|---|---|---|
| LO1 | (0.60 × 90 + 0.40 × 80) ÷ (0.60 + 0.40) | 86.0 |
| LO2 | (0.40 × 90 + 1.00 × 80) ÷ (0.40 + 1.00) | 82.9 |
| PO1 | (2 × 86.0 + 1 × 82.86) ÷ (2 + 1) | 85.0 |
| PO2 | (2 × 82.86) ÷ 2 | 82.9 |
| PO3 | bağlı LO yok | NULL |

Hocanın örneğindeki LO→PO ağırlıkları 1.0 : 0.5 : 1.0'dır. Modelde ağırlık 1–5 tam sayıdır, bu yüzden aynı oran 2 : 1 : 2 olarak girilir. Ağırlıklı ortalamada yalnızca oran önemli olduğundan sonuç aynıdır.

![Şekil 3 — Class diyagramı](../diagrams/class.png)
