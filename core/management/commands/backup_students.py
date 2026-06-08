import json
from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from students.models import Student


class Command(BaseCommand):
    help = 'Backup student class assignments before promote. Restore with --restore <file>'

    def add_arguments(self, parser):
        parser.add_argument('--restore', type=str, help='Restore from backup file')

    def handle(self, *args, **options):
        restore_file = options.get('restore')

        if restore_file:
            self._restore(restore_file)
        else:
            self._backup()

    def _backup(self):
        students = Student.objects.filter(deleted_at__isnull=True).select_related('school_class')
        data = []
        for s in students:
            data.append({
                'id': str(s.id),
                'name': s.name,
                'school_class_id': str(s.school_class_id) if s.school_class_id else None,
                'school_class_name': s.school_class.name if s.school_class else None,
                'session': s.session,
                'graduated_at': s.graduated_at.isoformat() if s.graduated_at else None,
            })

        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'student_backup_{ts}.json'
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

        self.stdout.write(self.style.SUCCESS(f'Backed up {len(data)} students to {filename}'))

    def _restore(self, filename):
        with open(filename) as f:
            data = json.load(f)

        restored = 0
        for record in data:
            try:
                s = Student.objects.get(id=record['id'])
                s.school_class_id = record.get('school_class_id')
                s.session = record.get('session', '')
                if record.get('graduated_at'):
                    s.graduated_at = record['graduated_at']
                else:
                    s.graduated_at = None
                s.save()
                restored += 1
            except Student.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'Student {record["id"]} not found, skipping'))

        self.stdout.write(self.style.SUCCESS(f'Restored {restored} students from {filename}'))
