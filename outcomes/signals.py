"""
Otomatik yeniden hesaplama tetikleyicileri.

Not, değerlendirme→LO eşlemesi ya da LO→PO ağırlığı eklenince, değişince veya
silinince yalnızca etkilenen öğrencilerin PO snapshot'ları yeniden hesaplanır.
"""
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Assessment_LO_Mapping, LO_PO_Mapping, StudentGrade, User
from .services import POCalculatorService


def _student_is_being_deleted(origin) -> bool:
    """Öğrencinin kendisi siliniyorsa (cascade) snapshot'ları da silinir; hesaplamaya gerek yok."""
    return isinstance(origin, User) or getattr(origin, 'model', None) is User


@receiver(post_save, sender=StudentGrade)
def recalculate_on_grade_save(sender, instance, raw=False, **kwargs):
    if raw:  # loaddata: fixture yüklenirken hesaplama yapma
        return
    POCalculatorService.calculate_student_profile(instance.student)


@receiver(post_delete, sender=StudentGrade)
def recalculate_on_grade_delete(sender, instance, origin=None, **kwargs):
    if _student_is_being_deleted(origin):
        return
    POCalculatorService.recalculate_students([instance.student_id])


@receiver(post_save, sender=Assessment_LO_Mapping)
@receiver(post_delete, sender=Assessment_LO_Mapping)
def recalculate_on_assessment_mapping_change(sender, instance, raw=False, **kwargs):
    if raw:
        return
    POCalculatorService.recalculate_students(
        POCalculatorService.students_with_grades_for_assessment(instance.assessment_id)
    )


@receiver(post_save, sender=LO_PO_Mapping)
@receiver(post_delete, sender=LO_PO_Mapping)
def recalculate_on_lo_po_mapping_change(sender, instance, raw=False, **kwargs):
    if raw:
        return
    POCalculatorService.recalculate_students(
        POCalculatorService.students_with_grades_for_lo(instance.learning_outcome_id)
    )
