from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import (
    Assessment,
    Assessment_LO_Mapping,
    Course,
    Enrollment,
    LearningOutcome,
    LO_PO_Mapping,
    ProgramOutcome,
    StudentGrade,
    StudentPOSnapshot,
    User,
)

admin.site.site_header = 'Waffle 5.1 — PO Yönetim Sistemi'
admin.site.site_title = 'Waffle 5.1'
admin.site.index_title = 'Yönetim'


# ------------------------------------------------------------------------------
# Satır içi (inline) düzenleyiciler
# ------------------------------------------------------------------------------
class LearningOutcomeInline(admin.TabularInline):
    model = LearningOutcome
    extra = 0


class AssessmentInline(admin.TabularInline):
    model = Assessment
    extra = 0


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    autocomplete_fields = ['student']


class AssessmentLOMappingInline(admin.TabularInline):
    model = Assessment_LO_Mapping
    extra = 0


class LOPOMappingInline(admin.TabularInline):
    model = LO_PO_Mapping
    extra = 0


# ------------------------------------------------------------------------------
# Kullanıcılar
# ------------------------------------------------------------------------------
@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'role', 'student_number', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'student_number')
    ordering = ('role', 'username')
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Rol', {'fields': ('role', 'student_number')}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('Rol', {'fields': ('role', 'student_number')}),
    )


# ------------------------------------------------------------------------------
# Program çıktıları, dersler, LO'lar
# ------------------------------------------------------------------------------
@admin.register(ProgramOutcome)
class ProgramOutcomeAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'mapped_lo_count')
    search_fields = ('code', 'title', 'description')

    @admin.display(description='Bağlı LO sayısı')
    def mapped_lo_count(self, obj):
        return obj.lo_mappings.count()


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'term', 'instructor', 'student_count')
    list_filter = ('term', 'instructor')
    search_fields = ('code', 'title')
    autocomplete_fields = ['instructor']
    inlines = [LearningOutcomeInline, AssessmentInline, EnrollmentInline]

    @admin.display(description='Öğrenci sayısı')
    def student_count(self, obj):
        return obj.enrollments.count()


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at')
    list_filter = ('course',)
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'student__student_number')
    autocomplete_fields = ['student', 'course']
    list_select_related = ('student', 'course')


@admin.register(LearningOutcome)
class LearningOutcomeAdmin(admin.ModelAdmin):
    list_display = ('code', 'course', 'description')
    list_filter = ('course',)
    search_fields = ('code', 'description', 'course__code')
    list_select_related = ('course',)
    inlines = [AssessmentLOMappingInline, LOPOMappingInline]


@admin.register(LO_PO_Mapping)
class LOPOMappingAdmin(admin.ModelAdmin):
    list_display = ('learning_outcome', 'program_outcome', 'weight')
    list_editable = ('weight',)
    list_filter = ('program_outcome', 'learning_outcome__course', 'weight')
    search_fields = ('learning_outcome__code', 'program_outcome__code')
    list_select_related = ('learning_outcome__course', 'program_outcome')


# ------------------------------------------------------------------------------
# Değerlendirmeler ve notlar
# ------------------------------------------------------------------------------
@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'max_score', 'grade_count')
    list_filter = ('course',)
    search_fields = ('name', 'course__code')
    list_select_related = ('course',)
    inlines = [AssessmentLOMappingInline]

    @admin.display(description='Girilen not sayısı')
    def grade_count(self, obj):
        return obj.grades.count()


@admin.register(Assessment_LO_Mapping)
class AssessmentLOMappingAdmin(admin.ModelAdmin):
    list_display = ('assessment', 'learning_outcome', 'weight')
    list_editable = ('weight',)
    list_filter = ('assessment__course',)
    search_fields = ('assessment__name', 'learning_outcome__code')
    list_select_related = ('assessment__course', 'learning_outcome__course')


@admin.register(StudentGrade)
class StudentGradeAdmin(admin.ModelAdmin):
    list_display = ('student', 'assessment', 'score', 'updated_at')
    list_editable = ('score',)
    list_filter = ('assessment__course', 'assessment')
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'student__student_number')
    autocomplete_fields = ['student']
    list_select_related = ('student', 'assessment__course')
    date_hierarchy = 'updated_at'


# ------------------------------------------------------------------------------
# Ön hesaplanmış PO profili: yalnızca okunur, hesaplama servisi yazar
# ------------------------------------------------------------------------------
@admin.register(StudentPOSnapshot)
class StudentPOSnapshotAdmin(admin.ModelAdmin):
    list_display = ('student', 'program_outcome', 'score_display', 'calculated_at')
    list_filter = ('program_outcome',)
    search_fields = ('student__username', 'student__first_name', 'student__last_name', 'student__student_number')
    list_select_related = ('student', 'program_outcome')
    readonly_fields = ('student', 'program_outcome', 'score', 'calculated_at')

    @admin.display(description='Puan', ordering='score')
    def score_display(self, obj):
        return 'veri yok' if obj.score is None else obj.score

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
