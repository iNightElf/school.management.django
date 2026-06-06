import json
import uuid
import base64
import urllib.request
from datetime import date, datetime
from decimal import Decimal

import psycopg2
from django.core.management.base import BaseCommand
from django.db import models
from django.utils import timezone

from core.models import SchoolClass, Subject, AcademicYear
from students.models import Student
from teachers.models import Teacher
from staff.models import Staff
from results.models import Result


FIREBASE_URL = "https://student-info-41f18-default-rtdb.asia-southeast1.firebasedatabase.app/school.json"

SUPABASE_DSN = (
    "postgresql://postgres.elpruxjzepvyhbtdlyck:%40nWPZjZ112358"
    "@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"
)

CLASS_KEY_MAP = {
    "play": "Play",
    "nursery": "Nursery",
    "kg": "KG",
    "one": "Class One",
    "two": "Class Two",
    "three": "Class Three",
    "four": "Class Four",
    "five": "Class Five",
}

CLASS_ORDER = {
    "Play": 0, "Nursery": 1, "KG": 2,
    "Class One": 3, "Class Two": 4, "Class Three": 5,
    "Class Four": 6, "Class Five": 7,
}

FIREBASE_TERM_MAP = {0: "Term 1", 1: "Term 2", 2: "Term 3"}


def fetch_firebase():
    resp = urllib.request.urlopen(FIREBASE_URL, timeout=30)
    return json.loads(resp.read().decode())


def fetch_supabase_photo_map():
    conn = psycopg2.connect(SUPABASE_DSN)
    cur = conn.cursor()
    mapping = {}
    for table in ["Student", "Teacher", "Staff"]:
        cur.execute(f'SELECT name, photo_path FROM "{table}"')
        for name, pp in cur.fetchall():
            if pp:
                mapping[name.strip().lower()] = pp
    conn.close()
    return mapping


class Command(BaseCommand):
    help = "Import students, teachers, staff, and results from Firebase + Supabase photos"

    def handle(self, *args, **options):
        self.stdout.write("Fetching Firebase data...")
        data = fetch_firebase()
        self.stdout.write("Fetching Supabase photo paths...")
        photo_map = fetch_supabase_photo_map()
        self.stdout.write(f"  Found {len(photo_map)} photo mappings")

        self._import_classes(data)
        self._import_academic_year()
        self._import_students(data, photo_map)
        self._import_teachers(data, photo_map)
        self._import_staff(data, photo_map)
        self._import_results(data)

        self.stdout.write(self.style.SUCCESS("Import complete!"))

    def _import_classes(self, data):
        self.stdout.write("Importing classes...")
        for name in data.get("classList", []):
            SchoolClass.objects.get_or_create(
                name=name, defaults={"order": CLASS_ORDER.get(name, 0)}
            )
        self.stdout.write(f"  {len(data.get('classList', []))} classes ready")

    def _import_academic_year(self):
        self.stdout.write("Creating academic year...")
        y = date.today().year
        AcademicYear.objects.get_or_create(
            name=f"FY{y}",
            defaults={"start_date": date(y, 1, 1), "end_date": date(y, 12, 31), "is_active": True},
        )

    def _find_photo(self, name, photo_map):
        key = name.strip().lower()
        return photo_map.get(key)

    def _import_students(self, data, photo_map):
        self.stdout.write("Importing students...")
        total = 0
        for fkey, slist in data.get("students", {}).items():
            class_name = CLASS_KEY_MAP.get(fkey)
            if not class_name:
                continue
            try:
                school_class = SchoolClass.objects.get(name=class_name)
            except SchoolClass.DoesNotExist:
                continue
            for s in slist:
                name = s.get("name", "").strip()
                if not name:
                    continue
                roll = s.get("roll", "")
                student_id = f"r{roll}" if roll else f"manual-{uuid.uuid4().hex[:8]}"
                photo = self._find_photo(name, photo_map)
                Student.objects.get_or_create(
                    student_id=student_id,
                    defaults={
                        "school_class": school_class,
                        "roll": roll,
                        "name": name,
                        "father_name": s.get("fatherName", ""),
                        "mother_name": s.get("motherName", ""),
                        "contact": s.get("contactNumber", ""),
                        "session": str(date.today().year),
                        "photo_path": photo,
                    },
                )
                total += 1
        self.stdout.write(f"  {total} students imported")

    def _import_teachers(self, data, photo_map):
        self.stdout.write("Importing teachers...")
        count = 0
        for t in data.get("teachers", []):
            name = t.get("name", "").strip()
            if not name:
                continue
            photo = self._find_photo(name, photo_map)
            _, created = Teacher.objects.get_or_create(
                name=name,
                designation=t.get("designation", ""),
                defaults={
                    "email": t.get("email", ""),
                    "contact": t.get("contactNumber", ""),
                    "photo_path": photo,
                },
            )
            if created:
                count += 1
        self.stdout.write(f"  {count} teachers imported")

    def _import_staff(self, data, photo_map):
        self.stdout.write("Importing staff...")
        count = 0
        for s in data.get("staff", []):
            name = s.get("name", "").strip()
            if not name:
                continue
            photo = self._find_photo(name, photo_map)
            if not photo:
                fb_photo = s.get("photo", "")
                if fb_photo:
                    photo = fb_photo
            _, created = Staff.objects.get_or_create(
                name=name,
                role=s.get("role", ""),
                defaults={
                    "email": s.get("email", ""),
                    "contact": s.get("contactNumber", ""),
                    "photo_path": photo,
                },
            )
            if created:
                count += 1
        self.stdout.write(f"  {count} staff imported")

    def _import_results(self, data):
        self.stdout.write("Importing results...")
        academic_year = AcademicYear.objects.filter(is_active=True).first()
        session = academic_year.name if academic_year else str(date.today().year)
        total = 0

        for fkey, class_results in data.get("results", {}).items():
            class_name = CLASS_KEY_MAP.get(fkey)
            if not class_name:
                continue
            try:
                school_class = SchoolClass.objects.get(name=class_name)
            except SchoolClass.DoesNotExist:
                continue

            subjects_list = class_results.get("subjects", [])
            for i, subj in enumerate(subjects_list):
                Subject.objects.get_or_create(
                    name=subj["name"],
                    school_class=school_class,
                    defaults={"full_marks": subj.get("fullMarks", 100), "order": i},
                )

            per_student = class_results.get("results", {})
            for skey, entry in per_student.items():
                if not isinstance(entry, dict):
                    continue
                terms = entry.get("terms", [])
                comment = entry.get("comment", "")
                attendance_data = entry.get("attendance", {})

                student = Student.objects.filter(
                    roll=skey, school_class=school_class
                ).exclude(deleted_at__isnull=False).first()
                if not student:
                    student = Student.objects.filter(
                        student_id__endswith=skey
                    ).exclude(deleted_at__isnull=False).first()
                if not student:
                    continue

                for i, term_data in enumerate(terms):
                    if not term_data or not isinstance(term_data, dict):
                        continue
                    term_name = FIREBASE_TERM_MAP.get(i, f"Term {i+1}")
                    att = attendance_data.get(str(i + 1)) if isinstance(attendance_data, dict) else None
                    _, created = Result.objects.get_or_create(
                        student=student,
                        term=term_name,
                        session=session,
                        defaults={
                            "marks": term_data,
                            "attendance": att,
                            "comment": comment,
                        },
                    )
                    if created:
                        total += 1

        self.stdout.write(f"  {total} result entries imported")
