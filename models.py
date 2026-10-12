from decimal import Decimal
from django.db import models, transaction
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


# ==============================================================================
# 1. KULLANICI & ROLLER (RBAC)
# ==============================================================================
class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Bölüm Başkanı / Yönetici'
        INSTRUCTOR = 'INSTRUCTOR', 'Öğretim Üyesi'
        STUDENT = 'STUDENT', 'Öğrenci'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    student_number = models.CharField(max_length=20, blank=True, null=True, unique=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"


# ==============================================================================
# 2. BÖLÜM VE PROGRAM ÇIKTILARI (PO 1..11)
# ==============================================================================
class ProgramOutcome(models.Model):
    code = models.CharField(max_length=10, unique=True)  # Örn: PO1, PO2, ..., PO11
    title = models.CharField(max_length=255)
    description = models.TextField()

    class Meta:
        ordering = ['code']

    def __str__(self):
        return f"{self.code} - {self.title}"


# ==============================================================================
# 3. DERS VE DERS ÇIKTILARI (COURSES & LEARNING OUTCOMES)
# ==============================================================================
class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)  # Örn: CSE 311
    title = models.CharField(max_length=255)
    term = models.CharField(max_length=50, default='Fall 2026')
    instructor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': User.Role.INSTRUCTOR},
        related_name='courses'
    )

    def __str__(self):
        return f"{self.code} - {self.title}"


class LearningOutcome(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='learning_outcomes')
    code = models.CharField(max_length=10)  # Örn: LO1, LO2
    description = models.TextField()

    class Meta:
        unique_together = ('course', 'code')
        ordering = ['course', 'code']

    def __str__(self):
        return f"{self.course.code} - {self.code}"


class LO_PO_Mapping(models.Model):
    """
    Her dersin Learning Outcome'ı, Program Outcome'a 1-5 arası bir ağırlıkla bağlanır.
    """
    learning_outcome = models.ForeignKey(LearningOutcome, on_delete=models.CASCADE, related_name='po_mappings')
    program_outcome = models.ForeignKey(ProgramOutcome, on_delete=models.CASCADE, related_name='lo_mappings')
    weight = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('5.00'))],
        help_text="1.0 ile 5.0 arasında ağırlık"
    )

    class Meta:
        unique_together = ('learning_outcome', 'program_outcome')
        indexes = [
            models.Index(fields=['learning_outcome', 'program_outcome']),
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
        unique_together = ('assessment', 'learning_outcome')

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
        unique_together = ('student', 'assessment')
        indexes = [
            models.Index(fields=['student', 'assessment']),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.assessment}: {self.score}"


# ==============================================================================
# 5. ÖN HESAPLANMIŞ PO PROFİLİ (CSE 321: PRE-COMPUTATION / CACHING)
# ==============================================================================
class StudentPOSnapshot(models.Model):
    """
    Her istekte devasa hesaplama yapmamak için öğrencinin PO skorlarını tutan snapshot tablosu.
    """
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='po_snapshots')
    program_outcome = models.ForeignKey(ProgramOutcome, on_delete=models.CASCADE, related_name='student_snapshots')
    score = models.DecimalField(max_digits=5, decimal_places=2)
    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'program_outcome')
        indexes = [
            models.Index(fields=['student', 'program_outcome']),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.program_outcome.code}: {self.score}"