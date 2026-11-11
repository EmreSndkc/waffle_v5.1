from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q


# ==============================================================================
# 1. KULLANICI & ROLLER (RBAC)
# ==============================================================================
class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Sistem Yöneticisi'
        DEPT_HEAD = 'DEPT_HEAD', 'Bölüm Başkanı'
        INSTRUCTOR = 'INSTRUCTOR', 'Öğretim Üyesi'
        STUDENT = 'STUDENT', 'Öğrenci'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    student_number = models.CharField(max_length=20, blank=True, null=True, unique=True)

    class Meta(AbstractUser.Meta):
        indexes = [
            # "Tüm öğrenciler / tüm hocalar" listeleri
            models.Index(fields=['role'], name='user_role_idx'),
        ]

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.role})"


# ==============================================================================
# 2. BÖLÜM VE PROGRAM ÇIKTILARI (PO 1..11)
# ==============================================================================
class ProgramOutcome(models.Model):
    code = models.CharField(max_length=10, unique=True)  # Örn: PO1, PO2, ..., PO11
    title = models.CharField(max_length=255)
    description = models.TextField()

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.code} - {self.title}"


# ==============================================================================
# 3. DERS, KAYIT VE DERS ÇIKTILARI (COURSES, ENROLLMENT & LEARNING OUTCOMES)
# ==============================================================================
class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)  # Örn: CSE 311
    title = models.CharField(max_length=255)
    term = models.CharField(max_length=50, default='Fall 2026')
    instructor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'role': User.Role.INSTRUCTOR},
        related_name='courses'
    )
    students = models.ManyToManyField(
        User,
        through='Enrollment',
        related_name='enrolled_courses',
        blank=True,
    )

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.title}"


class Enrollment(models.Model):
    """
    Öğrenci ↔ ders kaydı. Hangi öğrencinin hangi derste olduğunu tutar;
    not girme ekranı ve yeniden hesaplama bu tabloya göre çalışır.
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': User.Role.STUDENT},
        related_name='enrollments'
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'course'], name='uniq_enrollment_student_course'),
        ]
        indexes = [
            # Bir dersin öğrenci listesi (unique index öğrenci → ders yönünü karşılar)
            models.Index(fields=['course', 'student'], name='enroll_course_student_idx'),
        ]

    def __str__(self):
        return f"{self.student.username} @ {self.course.code}"


class LearningOutcome(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='learning_outcomes')
    code = models.CharField(max_length=10)  # Örn: LO1, LO2
    description = models.TextField()

    class Meta:
        ordering = ['course', 'code']
        constraints = [
            models.UniqueConstraint(fields=['course', 'code'], name='uniq_lo_course_code'),
        ]

    def __str__(self):
        return f"{self.course.code} - {self.code}"


class LO_PO_Mapping(models.Model):
    """
    Her dersin Learning Outcome'ı, Program Outcome'a 1-5 arası tam sayı bir ağırlıkla bağlanır.
    """
    learning_outcome = models.ForeignKey(LearningOutcome, on_delete=models.CASCADE, related_name='po_mappings')
    program_outcome = models.ForeignKey(ProgramOutcome, on_delete=models.CASCADE, related_name='lo_mappings')
    weight = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="1 ile 5 arasında tam sayı ağırlık"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['learning_outcome', 'program_outcome'], name='uniq_lo_po'),
            models.CheckConstraint(check=Q(weight__gte=1) & Q(weight__lte=5), name='lo_po_weight_1_5'),
        ]
        indexes = [
            # PO → LO yönü: "bu PO'yu hangi LO'lar besliyor?"
            models.Index(fields=['program_outcome', 'learning_outcome'], name='lo_po_po_lo_idx'),
        ]

    def __str__(self):
        return f"{self.learning_outcome} -> {self.program_outcome.code} (w: {self.weight})"


# ==============================================================================
# 4. DEĞERLENDİRMELER VE NOTLAR (ASSESSMENTS & GRADES)
# ==============================================================================
class Assessment(models.Model):
    """
    Ders içi değerlendirmeler: Midterm, Project, Final, Quiz vb.
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assessments')
    name = models.CharField(max_length=100)  # Örn: Midterm, Project
    max_score = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('100.0'))

    class Meta:
        ordering = ['course', 'id']
        constraints = [
            models.UniqueConstraint(fields=['course', 'name'], name='uniq_assessment_course_name'),
        ]

    def __str__(self):
        return f"{self.course.code} - {self.name}"


class Assessment_LO_Mapping(models.Model):
    """
    Bir değerlendirmenin hangi LO'yu ne ağırlıkla (yüzde/katsayı) etkilediği.
    Örn: Midterm -> LO1 %60 (0.60), LO2 %40 (0.40)
    """
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='lo_mappings')
    learning_outcome = models.ForeignKey(LearningOutcome, on_delete=models.CASCADE, related_name='assessment_mappings')
    weight = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Değerlendirmenin LO üzerindeki katsayısı/ağırlığı (Örn: 0.60 veya 1.0)"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['assessment', 'learning_outcome'], name='uniq_assessment_lo'),
            models.CheckConstraint(check=Q(weight__gt=0), name='assessment_lo_weight_positive'),
        ]
        indexes = [
            # LO → değerlendirme yönü: LO puanı hesaplanırken kullanılır
            models.Index(fields=['learning_outcome', 'assessment'], name='assess_lo_lo_assess_idx'),
        ]

    def __str__(self):
        return f"{self.assessment.name} -> {self.learning_outcome.code} (w: {self.weight})"


class StudentGrade(models.Model):
    """
    Öğrencinin bir değerlendirmeden aldığı ham not (0 - 100).
    """
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': User.Role.STUDENT},
        related_name='grades'
    )
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name='grades')
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))]
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'assessment'], name='uniq_grade_student_assessment'),
            models.CheckConstraint(check=Q(score__gte=0) & Q(score__lte=100), name='grade_score_0_100'),
        ]
        indexes = [
            # Bir değerlendirmenin tüm notları (not girme ekranı, sınıf ortalaması)
            models.Index(fields=['assessment', 'student'], name='grade_assess_student_idx'),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.assessment}: {self.score}"


# ==============================================================================
# 5. ÖN HESAPLANMIŞ PO PROFİLİ (CSE 321: PRE-COMPUTATION / CACHING)
# ==============================================================================
class StudentPOSnapshot(models.Model):
    """
    Her istekte devasa hesaplama yapmamak için öğrencinin PO skorlarını tutan snapshot tablosu.
    score = NULL: bu PO için henüz veri yok (0 puan değil).
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='po_snapshots')
    program_outcome = models.ForeignKey(ProgramOutcome, on_delete=models.CASCADE, related_name='student_snapshots')
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'program_outcome'], name='uniq_snapshot_student_po'),
        ]
        indexes = [
            # PO bazlı raporlar: "PO3 ortalaması", "PO3'te eşiğin altındaki öğrenciler"
            models.Index(fields=['program_outcome', 'score'], name='snapshot_po_score_idx'),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.program_outcome.code}: {self.score}"
