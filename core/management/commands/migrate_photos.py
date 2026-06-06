from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Migrate binary photos from DB to Supabase Storage (deprecated — photo binary field removed)"

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            "The `photo` BinaryField has been removed from Student, Teacher, and Staff models. "
            "Photos are now referenced via `photo_path` only. "
            "This migration command is no longer needed."
        ))
