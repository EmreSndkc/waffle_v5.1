from decimal import Decimal
from django.db import transaction
from .models import (
    User, Course, LearningOutcome, ProgramOutcome,
    Assessment_LO_Mapping, StudentGrade, LO_PO_Mapping, StudentPOSnapshot
)

class POCalculatorService:
    """
    Slaytlardaki ağırlıklı ortalama formülünü uygulayan ve sonuçları
    StudentPOSnapshot tablosuna kaydeden hesaplama servisi.
    """

    @classmethod
    @transaction.atomic
    def calculate_student_profile(cls, student: User):
        """
        Belirli bir öğrencinin tüm derslerindeki notlarını toplayarak
        11 Program Çıktısı (PO) puanını hesaplar ve snapshot'ı günceller.
        """
        # 1. Öğrencinin aldığı tüm notları çek (Assessment ID -> Score)
        grades = {
            g.assessment_id: g.score 
            for g in StudentGrade.objects.filter(student=student).select_related('assessment')
        }

        # 2. Her LO için puan hesapla: Sum(grade * weight) / Sum(weight)
        lo_scores = {}
        all_lo_mappings = Assessment_LO_Mapping.objects.select_related('assessment', 'learning_outcome').all()
        
        # LO bazlı gruplama
        lo_accumulator = {}  # lo_id: {'weighted_sum': Decimal, 'total_weight': Decimal}
        for mapping in all_lo_mappings:
            lo_id = mapping.learning_outcome_id
            if mapping.assessment_id in grades:
                score = grades[mapping.assessment_id]
                weight = mapping.weight

                if lo_id not in lo_accumulator:
                    lo_accumulator[lo_id] = {'weighted_sum': Decimal('0'), 'total_weight': Decimal('0')}

                lo_accumulator[lo_id]['weighted_sum'] += (score * weight)
                lo_accumulator[lo_id]['total_weight'] += weight

        for lo_id, data in lo_accumulator.items():
            if data['total_weight'] > Decimal('0'):
                lo_scores[lo_id] = data['weighted_sum'] / data['total_weight']

        # 3. Her PO için puan hesapla: Sum(lo_score * lo_po_weight) / Sum(lo_po_weight)
        all_pos = ProgramOutcome.objects.all()
        po_accumulator = {po.id: {'weighted_sum': Decimal('0'), 'total_weight': Decimal('0')} for po in all_pos}

        lo_po_mappings = LO_PO_Mapping.objects.select_related('learning_outcome', 'program_outcome').all()
        for mapping in lo_po_mappings:
            if mapping.learning_outcome_id in lo_scores:
                lo_score = lo_scores[mapping.learning_outcome_id]
                po_weight = mapping.weight

                po_accumulator[mapping.program_outcome_id]['weighted_sum'] += (lo_score * po_weight)
                po_accumulator[mapping.program_outcome_id]['total_weight'] += po_weight

        # 4. Sonuçları StudentPOSnapshot tablosuna atomic olarak yaz / güncelle
        snapshots_to_update = []
        for po in all_pos:
            data = po_accumulator[po.id]
            final_po_score = Decimal('0.00')
            if data['total_weight'] > Decimal('0'):
                final_po_score = round(data['weighted_sum'] / data['total_weight'], 2)

            StudentPOSnapshot.objects.update_or_create(
                student=student,
                program_outcome=po,
                defaults={'score': final_po_score}
            )

        return StudentPOSnapshot.objects.filter(student=student).select_related('program_outcome')