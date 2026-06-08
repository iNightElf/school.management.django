import json
import os
import urllib.request

from django.core.management.base import BaseCommand

from core.models import Subject, SchoolClass

FIREBASE_BASE = os.environ.get("FIREBASE_RESULTS_URL", "")

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
    help = "Set Subject.order to match Firebase subjects array position"

    def handle(self, *args, **options):
        for firebase_key, class_name in CLASS_KEY_MAP.items():
            school_class = SchoolClass.objects.filter(name=class_name).first()
            if not school_class:
                continue

            class_data = fetch_class_results(firebase_key)
            subjects_list = class_data.get("subjects", [])
            if not subjects_list:
                self.stdout.write(f"  {class_name}: no subjects data, skipping")
                continue

            updated = 0
            for idx, subj in enumerate(subjects_list):
                fb_name = subj["name"]
                canonical = SUBJECT_NAME_MAP.get(fb_name, fb_name)
                subject = Subject.objects.filter(
                    name=canonical, school_class=school_class
                ).first()
                if subject and subject.order != idx:
                    subject.order = idx
                    subject.save(update_fields=["order"])
                    updated += 1

            self.stdout.write(f"  {class_name}: set order on {updated} subjects")

        self.stdout.write(self.style.SUCCESS("Done."))
