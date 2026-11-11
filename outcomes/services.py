from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from typing import Dict, Iterable, Optional

from django.db import transaction

from .models import (
    Assessment,
    Assessment_LO_Mapping,
    LO_PO_Mapping,
    ProgramOutcome,
    StudentGrade,
    StudentPOSnapshot,
    User,
)

TWO_PLACES = Decimal('0.01')


def weighted_average(pairs: Iterable) -> Optional[Decimal]:
    """
    puan = Σ(ağırlık × puan) ÷ Σ ağırlık
    pairs: (ağırlık, puan) ikilileri. Hiç veri yoksa None döner (0 değil).
    """
    weighted_sum = Decimal('0')
    total_weight = Decimal('0')
    for weight, score in pairs:
        weight = Decimal(weight)
        weighted_sum += weight * Decimal(score)
        total_weight += weight
    if total_weight == 0:
        return None
    return weighted_sum / total_weight


class POCalculatorService:
    """
    Ağırlıklı ortalama formülünü iki adımda uygular (not → LO → PO) ve sonucu
    StudentPOSnapshot tablosuna yazar. Tüm yazmalar tek transaction içindedir.
    """

    # --------------------------------------------------------------------------
    # Saf hesaplama (veritabanına yazmaz)
    # --------------------------------------------------------------------------
    @staticmethod
    def calculate_lo_scores(student: User) -> Dict[int, Decimal]:
        """Adım 1: {learning_outcome_id: LO puanı}. Notu olmayan LO sözlükte yer almaz."""
        grades = dict(
            StudentGrade.objects.filter(student=student).values_list('assessment_id', 'score')
        )
        if not grades:
            return {}

        pairs_by_lo = defaultdict(list)
        mappings = Assessment_LO_Mapping.objects.filter(assessment_id__in=grades.keys())
        for assessment_id, lo_id, weight in mappings.values_list('assessment_id', 'learning_outcome_id', 'weight'):
            pairs_by_lo[lo_id].append((weight, grades[assessment_id]))

        return {lo_id: weighted_average(pairs) for lo_id, pairs in pairs_by_lo.items()}

    @staticmethod
    def calculate_po_scores(lo_scores: Dict[int, Decimal]) -> Dict[int, Optional[Decimal]]:
        """Adım 2: {program_outcome_id: PO puanı ya da None}. Her PO için bir kayıt döner."""
        pairs_by_po = defaultdict(list)
        mappings = LO_PO_Mapping.objects.filter(learning_outcome_id__in=lo_scores.keys())
        for lo_id, po_id, weight in mappings.values_list('learning_outcome_id', 'program_outcome_id', 'weight'):
            pairs_by_po[po_id].append((weight, lo_scores[lo_id]))

        result = {}
        for po_id in ProgramOutcome.objects.values_list('id', flat=True):
            score = weighted_average(pairs_by_po.get(po_id, []))
            result[po_id] = None if score is None else score.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)
        return result

    # --------------------------------------------------------------------------
    # Snapshot yazma
    # --------------------------------------------------------------------------
    @classmethod
    @transaction.atomic
    def calculate_student_profile(cls, student: User):
        """
        Öğrencinin tüm PO puanlarını yeniden hesaplar ve snapshot'ı günceller.
        Verisi olmayan PO'nun puanı NULL yazılır.

        Öğrenci satırı select_for_update ile kilitlenir: aynı öğrenci için eşzamanlı
        iki yeniden hesaplama sıraya girer, biri diğerinin eski sonucunu ezemez.
        """
        locked = User.objects.select_for_update().filter(pk=student.pk).first()
        if locked is None:
            return StudentPOSnapshot.objects.none()

        po_scores = cls.calculate_po_scores(cls.calculate_lo_scores(locked))
        for po_id, score in po_scores.items():
            StudentPOSnapshot.objects.update_or_create(
                student=locked,
                program_outcome_id=po_id,
                defaults={'score': score},
            )
        return StudentPOSnapshot.objects.filter(student=locked).select_related('program_outcome')

    @classmethod
    @transaction.atomic
    def recalculate_students(cls, student_ids: Iterable[int]) -> int:
        """Verilen öğrencileri hepsi-ya-hiç yeniden hesaplar; hesaplanan öğrenci sayısını döner."""
        count = 0
        # Sabit sırada kilitle: eşzamanlı toplu hesaplamalar birbirini kilitlemesin (deadlock)
        for student in User.objects.filter(pk__in=set(student_ids)).order_by('pk'):
            cls.calculate_student_profile(student)
            count += 1
        return count

    # --------------------------------------------------------------------------
    # Değişiklikten etkilenen öğrenciler
    # --------------------------------------------------------------------------
    @staticmethod
    def students_with_grades_for_assessment(assessment_id: int):
        return StudentGrade.objects.filter(assessment_id=assessment_id).values_list('student_id', flat=True)

    @staticmethod
    def students_with_grades_for_lo(learning_outcome_id: int):
        return StudentGrade.objects.filter(
            assessment__lo_mappings__learning_outcome_id=learning_outcome_id
        ).values_list('student_id', flat=True).distinct()

    # --------------------------------------------------------------------------
    # Not kaydı: not + yeniden hesaplama tek transaction
    # --------------------------------------------------------------------------
    @classmethod
    @transaction.atomic
    def save_grade(cls, student: User, assessment: Assessment, score) -> StudentGrade:
        """
        Notu kaydeder; PO'lar aynı transaction içinde (signal ile) yeniden hesaplanır.
        Hesaplama hata verirse not da geri alınır.
        """
        grade = (
            StudentGrade.objects.select_for_update()
            .filter(student=student, assessment=assessment)
            .first()
        ) or StudentGrade(student=student, assessment=assessment)
        grade.score = Decimal(str(score))
        grade.full_clean()
        grade.save()
        return grade
