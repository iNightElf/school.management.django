import json
import urllib.request

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import SchoolClass
from students.models import Student
from results.models import Result


FIREBASE_BASE = "https://student-info-41f18-default-rtdb.asia-southeast1.firebasedatabase.app/school/results"

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

SUBJECT_NAME_MAP = {
    "Quran Learning": "Religion and Quran Learning",
    "Religion & Quran Learning": "Religion and Quran Learning",
    "General knowledge": "General Knowledge",
}


def fetch_class_results(firebase_key: str):
    url = f"{FIREBASE_BASE}/{firebase_key}.json"
    resp = urllib.request.urlopen(url, timeout=30)
    return json.loads(resp.read().decode())


class Command(BaseCommand):
    help = "Import 1st Term result marks from Firebase terms[1] into the new app"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview what would be imported without writing to DB",
        )
        parser.add_argument(
            "--session",
            default="FY2026",
            help="Academic session to assign (default: FY2026)",
        )
        parser.add_argument(
            "--term",
            default="1",
            help="Term label to save as (default: 1)",
        )
        parser.add_argument(
            "--firebase-index",
            type=int,
            default=1,
            help="Firebase terms array index to read marks from (default: 1)",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        session = options["session"]
        term = options["term"]
        fb_idx = options["firebase_index"]

        self.stdout.write(f"Session: {session}, Term: {term}" + ("  [DRY RUN]" if dry_run else ""))
        self.stdout.write("")

        total_created = 0
        total_updated = 0
        total_skipped_no_marks = 0
        total_skipped_no_student = 0
        total_attendance = 0
        total_comments = 0

        for firebase_key, class_name in CLASS_KEY_MAP.items():
            school_class = SchoolClass.objects.filter(name=class_name).first()
            if not school_class:
                self.stdout.write(f"  WARNING: Class '{class_name}' not found, skipping")
                continue

            self.stdout.write(f"\n--- {class_name} ---")

            class_data = fetch_class_results(firebase_key)
            per_student = class_data.get("results", {})
            if not per_student:
                self.stdout.write(f"  No results data")
                continue

            # Collect known student IDs for this class for fast lookup
            class_students = {
                s.student_id: s for s in Student.objects.filter(
                    school_class=school_class, deleted_at__isnull=True
                )
            }

            for student_key, entry in per_student.items():
                if not isinstance(entry, dict):
                    continue

                terms = entry.get("terms", [])
                if len(terms) <= fb_idx or not isinstance(terms[fb_idx], dict):
                    total_skipped_no_marks += 1
                    continue

                marks_raw = terms[fb_idx]
                # Normalize subject names
                marks = {}
                for k, v in marks_raw.items():
                    normalized = SUBJECT_NAME_MAP.get(k, k)
                    marks[normalized] = v

                # Find student
                student = class_students.get(student_key)
                if not student:
                    # Fallback: try by roll (strip r prefix and look for integer match)
                    if student_key.startswith("r"):
                        roll_part = student_key[1:]
                        student = Student.objects.filter(
                            school_class=school_class, roll=roll_part,
                            deleted_at__isnull=True
                        ).first()
                if not student:
                    # Fallback: try by name (Firebase keys like ntaskin_shahriyer)
                    name_key = student_key.lstrip("n").replace("_", " ").strip()
                    if name_key:
                        student = Student.objects.filter(
                            school_class=school_class, name__icontains=name_key,
                            deleted_at__isnull=True
                        ).first()
                if not student:
                    total_skipped_no_student += 1
                    if total_skipped_no_student <= 3:
                        self.stdout.write(f"  WARNING: Student '{student_key}' not found in {class_name}")
                    continue

                attendance = entry.get("attendance")
                comment = entry.get("comment", "")

                if dry_run:
                    self.stdout.write(
                        f"  Would update {student.name}: {len(marks)} subjects"
                        + (f", attendance" if attendance else "")
                        + (f", comment" if comment else "")
                    )
                    total_created += 1
                    if attendance:
                        total_attendance += 1
                    if comment:
                        total_comments += 1
                    continue

                with transaction.atomic():
                    result, created = Result.objects.update_or_create(
                        student=student,
                        term=term,
                        session=session,
                        defaults={
                            "marks": marks,
                            "attendance": attendance if attendance else None,
                            "comment": comment or "",
                        },
                    )
                if created:
                    total_created += 1
                else:
                    total_updated += 1
                if attendance:
                    total_attendance += 1
                if comment:
                    total_comments += 1

        self.stdout.write("")
        self.stdout.write("=" * 50)
        if dry_run:
            self.stdout.write(f"DRY RUN — would import {total_created} results")
        else:
            self.stdout.write(f"Created: {total_created}")
            self.stdout.write(f"Updated: {total_updated}")
        self.stdout.write(f"Skipped (no marks): {total_skipped_no_marks}")
        self.stdout.write(f"Skipped (student not found): {total_skipped_no_student}")
        self.stdout.write(f"With attendance: {total_attendance}")
        self.stdout.write(f"With comments: {total_comments}")
