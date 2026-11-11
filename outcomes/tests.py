from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import (
    Assessment,
    Assessment_LO_Mapping,
    Course,
    LearningOutcome,
    LO_PO_Mapping,
    ProgramOutcome,
    StudentGrade,
    StudentPOSnapshot,
    User,
)
from .services import POCalculatorService, weighted_average

ONE_PLACE = Decimal('0.1')


def one_place(value):
    return value.quantize(ONE_PLACE)


class InstructorExampleMixin:
    """
    Hocanın örneği:
      Midterm 90, Project 80
      Midterm→LO1 %60, Project→LO1 %40, Midterm→LO2 %40, Project→LO2 %100
      LO1→PO1 1.0, LO2→PO1 0.5, LO2→PO2 1.0
    LO→PO ağırlıkları modelde 1–5 tam sayı olduğu için aynı oran 2 : 1 : 2 olarak girilir
    (ağırlıklı ortalamada yalnızca oran önemlidir).
    """

    @classmethod
    def setUpTestData(cls):
        cls.student = User.objects.create_user('elif', role=User.Role.STUDENT)
        cls.course = Course.objects.create(code='CSE 311', title='Software Engineering')
        cls.po1 = ProgramOutcome.objects.create(code='PO1', title='PO1', description='-')
        cls.po2 = ProgramOutcome.objects.create(code='PO2', title='PO2', description='-')
        cls.po3 = ProgramOutcome.objects.create(code='PO3', title='PO3', description='-')
        cls.lo1 = LearningOutcome.objects.create(course=cls.course, code='LO1', description='-')
        cls.lo2 = LearningOutcome.objects.create(course=cls.course, code='LO2', description='-')
        cls.midterm = Assessment.objects.create(course=cls.course, name='Midterm')
        cls.project = Assessment.objects.create(course=cls.course, name='Project')

        Assessment_LO_Mapping.objects.create(assessment=cls.midterm, learning_outcome=cls.lo1, weight=Decimal('0.60'))
        Assessment_LO_Mapping.objects.create(assessment=cls.project, learning_outcome=cls.lo1, weight=Decimal('0.40'))
        Assessment_LO_Mapping.objects.create(assessment=cls.midterm, learning_outcome=cls.lo2, weight=Decimal('0.40'))
        Assessment_LO_Mapping.objects.create(assessment=cls.project, learning_outcome=cls.lo2, weight=Decimal('1.00'))

        cls.lo1_po1 = LO_PO_Mapping.objects.create(learning_outcome=cls.lo1, program_outcome=cls.po1, weight=2)
        cls.lo2_po1 = LO_PO_Mapping.objects.create(learning_outcome=cls.lo2, program_outcome=cls.po1, weight=1)
        cls.lo2_po2 = LO_PO_Mapping.objects.create(learning_outcome=cls.lo2, program_outcome=cls.po2, weight=2)

    def enter_example_grades(self):
        StudentGrade.objects.create(student=self.student, assessment=self.midterm, score=90)
        StudentGrade.objects.create(student=self.student, assessment=self.project, score=80)

    def snapshot(self, po):
        return StudentPOSnapshot.objects.get(student=self.student, program_outcome=po).score


class WeightedAverageTests(TestCase):
    def test_formula(self):
        self.assertEqual(weighted_average([(Decimal('0.6'), 90), (Decimal('0.4'), 80)]), Decimal('86'))

    def test_no_data_is_none_not_zero(self):
        self.assertIsNone(weighted_average([]))


class InstructorExampleTests(InstructorExampleMixin, TestCase):
    """Kabul testi: LO1 = 86.0, LO2 = 82.9, PO1 = 85.0, PO2 = 82.9."""

    def test_lo_scores(self):
        self.enter_example_grades()
        lo_scores = POCalculatorService.calculate_lo_scores(self.student)
        self.assertEqual(one_place(lo_scores[self.lo1.id]), Decimal('86.0'))
        self.assertEqual(one_place(lo_scores[self.lo2.id]), Decimal('82.9'))

    def test_po_scores(self):
        self.enter_example_grades()
        POCalculatorService.calculate_student_profile(self.student)
        self.assertEqual(one_place(self.snapshot(self.po1)), Decimal('85.0'))
        self.assertEqual(one_place(self.snapshot(self.po2)), Decimal('82.9'))

    def test_po_without_data_is_null(self):
        """PO3'e hiçbir LO bağlı değil: puan 0 değil NULL olmalı."""
        self.enter_example_grades()
        POCalculatorService.calculate_student_profile(self.student)
        self.assertIsNone(self.snapshot(self.po3))

    def test_student_without_grades_has_all_null(self):
        snapshots = POCalculatorService.calculate_student_profile(self.student)
        self.assertEqual(snapshots.count(), 3)
        self.assertTrue(all(s.score is None for s in snapshots))


class AutoRecalculationTests(InstructorExampleMixin, TestCase):
    """Not, eşleme ya da ağırlık değişince snapshot kendiliğinden güncellenir."""

    def test_saving_grades_triggers_calculation(self):
        self.enter_example_grades()  # servis elle çağrılmıyor
        self.assertEqual(one_place(self.snapshot(self.po1)), Decimal('85.0'))
        self.assertEqual(one_place(self.snapshot(self.po2)), Decimal('82.9'))

    def test_grade_update_recalculates(self):
        self.enter_example_grades()
        POCalculatorService.save_grade(self.student, self.midterm, 100)
        # LO1 = 92, LO2 = 120/1.4 = 85.71; PO1 = (2×92 + 85.71)/3 = 89.90
        self.assertEqual(self.snapshot(self.po1), Decimal('89.90'))
        self.assertEqual(self.snapshot(self.po2), Decimal('85.71'))

    def test_grade_delete_returns_to_null(self):
        self.enter_example_grades()
        StudentGrade.objects.filter(student=self.student).delete()
        self.assertIsNone(self.snapshot(self.po1))
        self.assertIsNone(self.snapshot(self.po2))

    def test_lo_po_weight_change_recalculates(self):
        self.enter_example_grades()
        self.lo2_po1.weight = 2  # LO1 ve LO2 artık eşit ağırlıkta
        self.lo2_po1.save()
        # PO1 = (86 + 82.857)/2 = 84.43
        self.assertEqual(self.snapshot(self.po1), Decimal('84.43'))

    def test_assessment_lo_weight_change_recalculates(self):
        self.enter_example_grades()
        mapping = Assessment_LO_Mapping.objects.get(assessment=self.project, learning_outcome=self.lo2)
        mapping.weight = Decimal('0.60')  # LO2 = (0.4×90 + 0.6×80)/1.0 = 84
        mapping.save()
        self.assertEqual(self.snapshot(self.po2), Decimal('84.00'))

    def test_mapping_delete_recalculates(self):
        self.enter_example_grades()
        self.lo2_po2.delete()
        self.assertIsNone(self.snapshot(self.po2))

    def test_deleting_student_does_not_fail(self):
        self.enter_example_grades()
        self.student.delete()
        self.assertFalse(StudentPOSnapshot.objects.exists())

    def test_invalid_grade_is_rejected_and_snapshot_unchanged(self):
        self.enter_example_grades()
        with self.assertRaises(ValidationError):
            POCalculatorService.save_grade(self.student, self.midterm, 150)
        self.assertEqual(one_place(self.snapshot(self.po1)), Decimal('85.0'))


class WeightValidationTests(InstructorExampleMixin, TestCase):
    def test_lo_po_weight_must_be_between_1_and_5(self):
        for bad in (0, 6):
            mapping = LO_PO_Mapping(learning_outcome=self.lo1, program_outcome=self.po3, weight=bad)
            with self.assertRaises(ValidationError):
                mapping.full_clean()
