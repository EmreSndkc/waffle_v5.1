"""
Demo verisi:  python manage.py seed_demo

Tekrar çalıştırılabilir (idempotent): var olan kayıtları günceller, kopya üretmez.
"""
import random
from decimal import Decimal

from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from outcomes.models import (
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
from outcomes.services import POCalculatorService

# Yalnızca yerel demo içindir; gerçek ortamda --password ile değiştirin.
DEMO_PASSWORD = 'waffle-demo-2026'

# 11 Program Çıktısı (MÜDEK ölçütlerine göre mühendislik programı çıktıları, kısaltılmış).
# TODO: Bölümün resmi PO metniyle birebir karşılaştırılacak.
PROGRAM_OUTCOMES = [
    ('PO1', 'Matematik, fen ve mühendislik bilgisi',
     'Matematik, fen bilimleri ve bilgisayar mühendisliğine özgü konularda yeterli bilgi birikimi; bu bilgileri karmaşık mühendislik problemlerinde kullanabilme.'),
    ('PO2', 'Problem tanımlama ve çözme',
     'Karmaşık mühendislik problemlerini tanımlama, formüle etme ve çözme; bu amaçla uygun analiz ve modelleme yöntemlerini seçip uygulama.'),
    ('PO3', 'Tasarım',
     'Karmaşık bir sistemi, süreci veya ürünü gerçekçi kısıtlar ve koşullar altında, belirli gereksinimleri karşılayacak şekilde tasarlama.'),
    ('PO4', 'Modern araç kullanımı',
     'Mühendislik uygulamalarında karşılaşılan problemler için gerekli modern teknik ve araçları seçme, kullanma; bilişim teknolojilerini etkin kullanma.'),
    ('PO5', 'Deney tasarlama ve veri analizi',
     'Mühendislik problemlerinin incelenmesi için deney tasarlama, deney yapma, veri toplama, sonuçları analiz etme ve yorumlama.'),
    ('PO6', 'Takım çalışması',
     'Disiplin içi ve çok disiplinli takımlarda etkin biçimde çalışabilme; bireysel çalışma becerisi.'),
    ('PO7', 'İletişim',
     'Sözlü ve yazılı etkin iletişim kurma; en az bir yabancı dil bilgisi; etkin rapor yazma, sunum yapma, açık talimat verme ve alma.'),
    ('PO8', 'Yaşam boyu öğrenme',
     'Yaşam boyu öğrenmenin gerekliliği bilinci; bilgiye erişebilme, bilim ve teknolojideki gelişmeleri izleme ve kendini sürekli yenileme.'),
    ('PO9', 'Etik ve mesleki sorumluluk',
     'Etik ilkelerine uygun davranma, mesleki ve etik sorumluluk bilinci; mühendislik uygulamalarında kullanılan standartlar hakkında bilgi.'),
    ('PO10', 'Proje yönetimi ve girişimcilik',
     'Proje yönetimi, risk yönetimi ve değişiklik yönetimi gibi iş hayatındaki uygulamalar hakkında bilgi; girişimcilik, yenilikçilik ve sürdürülebilir kalkınma hakkında farkındalık.'),
    ('PO11', 'Toplumsal etki',
     'Mühendislik uygulamalarının evrensel ve toplumsal boyutlarda sağlık, çevre ve güvenlik üzerindeki etkileri; mühendislik çözümlerinin hukuksal sonuçları konusunda farkındalık.'),
]

# rol → (kullanıcı adı, ad, soyad, is_staff, is_superuser)
STAFF_USERS = [
    (User.Role.ADMIN, 'admin', 'Sistem', 'Yöneticisi', True, True),
    (User.Role.DEPT_HEAD, 'baskan', 'Deniz', 'Başkan', True, False),
    (User.Role.INSTRUCTOR, 'hoca.yazilim', 'Ahmet', 'Yazılım', True, False),
    (User.Role.INSTRUCTOR, 'hoca.veri', 'Ayşe', 'Veri', True, False),
    (User.Role.INSTRUCTOR, 'hoca.mat', 'Mehmet', 'Analiz', True, False),
]

# (kullanıcı adı, ad, soyad, öğrenci no). Elif hocanın örneğindeki öğrencidir.
STUDENTS = [
    ('elif', 'Elif', 'Örnek', '20230001'),
    ('can', 'Can', 'Demir', '20230002'),
    ('zeynep', 'Zeynep', 'Kaya', '20230003'),
    ('mert', 'Mert', 'Yıldız', '20230004'),
    ('selin', 'Selin', 'Aydın', '20230005'),
    ('emir', 'Emir', 'Çelik', '20230006'),
]

# Ders tanımları. assessment_lo: (değerlendirme, LO, katsayı); lo_po: (LO, PO, ağırlık 1–5)
COURSES = [
    {
        # Hocanın örneği: Midterm→LO1 %60, Project→LO1 %40, Midterm→LO2 %40, Project→LO2 %100;
        # LO1→PO1 1.0, LO2→PO1 0.5, LO2→PO2 1.0  (tam sayı karşılığı 2 : 1 : 2)
        'code': 'CSE 311', 'title': 'Software Engineering', 'instructor': 'hoca.yazilim',
        'los': [('LO1', 'Yazılım gereksinimlerini analiz eder ve modeller.'),
                ('LO2', 'Bir yazılım projesini takım halinde tasarlar ve gerçekleştirir.')],
        'assessments': ['Midterm', 'Project'],
        'assessment_lo': [('Midterm', 'LO1', '0.60'), ('Project', 'LO1', '0.40'),
                          ('Midterm', 'LO2', '0.40'), ('Project', 'LO2', '1.00')],
        'lo_po': [('LO1', 'PO1', 2), ('LO2', 'PO1', 1), ('LO2', 'PO2', 2)],
    },
    {
        'code': 'CSE 321', 'title': 'Data Systems', 'instructor': 'hoca.veri',
        'los': [('LO1', 'İlişkisel veri modeli tasarlar ve normalize eder.'),
                ('LO2', 'Index, transaction ve tutarlılık kavramlarını uygular.'),
                ('LO3', 'Ölçeklenebilir bir veri mimarisini raporlar ve sunar.')],
        'assessments': ['Midterm', 'Project', 'Final'],
        'assessment_lo': [('Midterm', 'LO1', '0.50'), ('Final', 'LO1', '0.50'),
                          ('Midterm', 'LO2', '0.30'), ('Final', 'LO2', '0.70'),
                          ('Project', 'LO3', '1.00')],
        'lo_po': [('LO1', 'PO3', 5), ('LO2', 'PO3', 3), ('LO2', 'PO4', 4),
                  ('LO3', 'PO6', 4), ('LO3', 'PO7', 3)],
    },
    {
        'code': 'MAT 241', 'title': 'Linear Algebra', 'instructor': 'hoca.mat',
        'los': [('LO1', 'Doğrusal denklem sistemlerini çözer.'),
                ('LO2', 'Özdeğer ve özvektör problemlerini modeller.')],
        'assessments': ['Midterm', 'Final'],
        'assessment_lo': [('Midterm', 'LO1', '0.70'), ('Final', 'LO1', '0.30'),
                          ('Midterm', 'LO2', '0.20'), ('Final', 'LO2', '0.80')],
        'lo_po': [('LO1', 'PO1', 5), ('LO2', 'PO1', 4), ('LO2', 'PO2', 3)],
    },
]

# Rol grupları: admin panelinde hangi rol hangi modeli değiştirebilir
OUTCOME_MODELS = ['programoutcome', 'course', 'enrollment', 'learningoutcome', 'lo_po_mapping',
                  'assessment', 'assessment_lo_mapping', 'studentgrade', 'studentposnapshot', 'user']
GROUPS = {
    'Bölüm Başkanı': {
        'edit': ['programoutcome', 'course', 'enrollment'],
        'view': OUTCOME_MODELS,
    },
    'Öğretim Üyesi': {
        'edit': ['learningoutcome', 'lo_po_mapping', 'assessment', 'assessment_lo_mapping', 'studentgrade'],
        'view': [m for m in OUTCOME_MODELS if m != 'user'],
    },
}
ROLE_GROUP = {User.Role.DEPT_HEAD: 'Bölüm Başkanı', User.Role.INSTRUCTOR: 'Öğretim Üyesi'}


class Command(BaseCommand):
    help = 'Demo verisi yükler: 11 PO, 3 ders, LO/değerlendirme/eşlemeler, her rol için kullanıcı, hocanın örneği.'

    def add_arguments(self, parser):
        parser.add_argument('--password', default=DEMO_PASSWORD, help='Demo kullanıcılarının parolası')

    @transaction.atomic
    def handle(self, *args, **options):
        password = options['password']

        for code, title, description in PROGRAM_OUTCOMES:
            ProgramOutcome.objects.update_or_create(code=code, defaults={'title': title, 'description': description})

        groups = self._seed_groups()
        users = {}
        for role, username, first, last, is_staff, is_superuser in STAFF_USERS:
            users[username] = self._seed_user(username, first, last, role, password,
                                              is_staff=is_staff, is_superuser=is_superuser)
            if role in ROLE_GROUP:
                users[username].groups.set([groups[ROLE_GROUP[role]]])
        students = [
            self._seed_user(username, first, last, User.Role.STUDENT, password, student_number=number)
            for username, first, last, number in STUDENTS
        ]
        elif_user, others = students[0], students[1:]

        rng = random.Random(321)  # her çalıştırmada aynı notlar
        for spec in COURSES:
            course, _ = Course.objects.update_or_create(
                code=spec['code'],
                defaults={'title': spec['title'], 'term': 'Fall 2026', 'instructor': users[spec['instructor']]},
            )
            los = {
                code: LearningOutcome.objects.update_or_create(course=course, code=code, defaults={'description': d})[0]
                for code, d in spec['los']
            }
            assessments = {
                name: Assessment.objects.get_or_create(course=course, name=name)[0]
                for name in spec['assessments']
            }
            for assessment_name, lo_code, weight in spec['assessment_lo']:
                Assessment_LO_Mapping.objects.update_or_create(
                    assessment=assessments[assessment_name], learning_outcome=los[lo_code],
                    defaults={'weight': Decimal(weight)},
                )
            for lo_code, po_code, weight in spec['lo_po']:
                LO_PO_Mapping.objects.update_or_create(
                    learning_outcome=los[lo_code], program_outcome=ProgramOutcome.objects.get(code=po_code),
                    defaults={'weight': weight},
                )

            # Elif yalnızca CSE 311'e kayıtlı: PO profili hocanın örneğiyle birebir aynı çıkar.
            enrolled = others + ([elif_user] if spec['code'] == 'CSE 311' else [])
            for student in enrolled:
                Enrollment.objects.get_or_create(student=student, course=course)
                for name, assessment in assessments.items():
                    if student == elif_user:
                        score = {'Midterm': 90, 'Project': 80}[name]
                    else:
                        score = rng.randint(45, 98)
                    StudentGrade.objects.update_or_create(
                        student=student, assessment=assessment, defaults={'score': Decimal(score)},
                    )

        POCalculatorService.recalculate_students([s.pk for s in students])

        self.stdout.write(self.style.SUCCESS(
            f'Seed tamam: {ProgramOutcome.objects.count()} PO, {Course.objects.count()} ders, '
            f'{LearningOutcome.objects.count()} LO, {Assessment.objects.count()} değerlendirme, '
            f'{User.objects.count()} kullanıcı, {StudentGrade.objects.count()} not, '
            f'{StudentPOSnapshot.objects.count()} snapshot.'
        ))
        profile = {
            s.program_outcome.code: s.score
            for s in StudentPOSnapshot.objects.filter(student=elif_user).select_related('program_outcome')
        }
        self.stdout.write(f"Elif (Midterm 90, Project 80): PO1 = {profile['PO1']}, PO2 = {profile['PO2']}, "
                          f"PO3 = {profile['PO3'] if profile['PO3'] is not None else 'NULL (veri yok)'}")
        self.stdout.write('Demo kullanıcıları: ' + ', '.join(
            f'{u.username} ({u.role})' for u in User.objects.order_by('role', 'username')
        ))

    def _seed_user(self, username, first, last, role, password, **extra):
        user, _ = User.objects.update_or_create(
            username=username,
            defaults={'first_name': first, 'last_name': last, 'role': role,
                      'email': f'{username}@example.com', **extra},
        )
        user.set_password(password)
        user.save(update_fields=['password'])
        return user

    def _seed_groups(self):
        groups = {}
        for name, rules in GROUPS.items():
            group, _ = Group.objects.get_or_create(name=name)
            codenames = [f'view_{m}' for m in rules['view']]
            for model in rules['edit']:
                codenames += [f'add_{model}', f'change_{model}', f'delete_{model}']
            group.permissions.set(
                Permission.objects.filter(content_type__app_label='outcomes', codename__in=codenames)
            )
            groups[name] = group
        return groups
