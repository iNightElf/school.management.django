import logging
from datetime import datetime, timezone
from django.db import transaction as db_transaction
from students.models import Student
from core.models import SchoolClass

logger = logging.getLogger(__name__)

MAX_CLASS_ORDER = 12

CLASS_NAMES = {
    8: 'Class Six', 9: 'Class Seven', 10: 'Class Eight',
    11: 'Class Nine', 12: 'Class Ten',
}


def _parse_student_roll(student_id):
    """Parse r{year}{classNum}{roll} format. Returns (year, class_num, roll) or None."""
    if not student_id or not isinstance(student_id, str):
        return None
    s = student_id.strip()
    if not s.startswith('r') or len(s) < 7:
        return None
    body = s[1:]
    if len(body) == 7:
        year = body[:4]
        class_num = int(body[4])
        roll = body[5:7]
    elif len(body) == 8:
        year = body[:4]
        class_num = int(body[4:6])
        roll = body[6:8]
    else:
        return None
    return year, class_num, roll


def _generate_student_roll(year, class_num, roll):
    """Generate r{year}{classNum:02d}{roll} format."""
    return f'r{year}{class_num:02d}{roll}'


def promote_all(data, is_dry_run=False):
    """Execute end-of-year student promotion.

    Returns dict with keys: promoted, graduated, classesCreated, error.
    """
    now = datetime.now(timezone.utc)

    if 'from_class_id' in data and 'to_class_id' in data:
        return _simple_promote(data, is_dry_run)

    target_year_name = data.get('targetYearName')
    target_year = int(target_year_name) if target_year_name and target_year_name.isdigit() else None

    classes = list(SchoolClass.objects.order_by('order', 'name'))
    if not classes:
        return {'error': 'No classes found. Create classes before promoting.'}

    promoted = []
    graduated = []
    classes_created = []

    class_by_order = {cls.order: cls for cls in classes}

    moves = []
    grads = []
    new_rolls = {}

    for cls in classes:
        students = list(Student.objects.filter(
            school_class=cls, deleted_at__isnull=True,
            graduated_at__isnull=True,
        ))
        if not students:
            continue

        next_order = cls.order + 1

        if next_order > MAX_CLASS_ORDER:
            grads.append((cls, students))
            continue

        next_class = class_by_order.get(next_order)
        if not next_class and not is_dry_run:
            name = CLASS_NAMES.get(next_order, f'Class {next_order}')
            next_class = SchoolClass.objects.create(name=name, order=next_order)
            class_by_order[next_order] = next_class
            classes_created.append(name)
        elif not next_class:
            name = CLASS_NAMES.get(next_order, f'Class {next_order}')
            classes_created.append(name)

        promoted.append({
            'from': cls.name,
            'to': next_class.name if next_class else CLASS_NAMES.get(next_order, f'Class {next_order}'),
            'count': len(students),
        })
        moves.append((cls, next_class, students))

        for s in students:
            parsed = _parse_student_roll(s.student_id)
            if parsed and target_year:
                old_year, old_class_num, old_roll = parsed
                new_class_num = old_class_num + 1
                new_id = _generate_student_roll(target_year, new_class_num, old_roll)
                new_rolls[s.id] = (new_id, next_order)

    for cls, students in grads:
        graduation_class_num = cls.order + 1
        for s in students:
            parsed = _parse_student_roll(s.student_id)
            if parsed and target_year:
                _, _, old_roll = parsed
                new_id = _generate_student_roll(target_year, graduation_class_num, old_roll)
                new_rolls[s.id] = (new_id, cls.order)

    if not is_dry_run:
        for cls, next_class, students in moves:
            for s in students:
                s.school_class = next_class
            Student.objects.bulk_update(students, ['school_class'])

        for cls, students in grads:
            for s in students:
                s.graduated_at = now
                s.school_class = None
            Student.objects.bulk_update(students, ['graduated_at', 'school_class'])

        if new_rolls:
            students_to_update = Student.objects.filter(id__in=new_rolls.keys())
            for s in students_to_update:
                new_id, _ = new_rolls[s.id]
                s.student_id = new_id
            Student.objects.bulk_update(students_to_update, ['student_id'])

        if target_year_name:
            Student.objects.filter(deleted_at__isnull=True).update(
                session=target_year_name,
            )

    return {
        'promoted': promoted,
        'graduated': [{'from': cls.name, 'count': len(students)} for cls, students in grads],
        'classesCreated': classes_created,
    }


def _simple_promote(data, is_dry_run):
    """Simple class-to-class promotion."""
    from_id = data['from_class_id']
    to_id = data['to_class_id']
    if not is_dry_run:
        Student.objects.filter(
            school_class_id=from_id, deleted_at__isnull=True
        ).update(school_class_id=to_id)
    from_name = SchoolClass.objects.filter(id=from_id).values_list('name', flat=True).first() or str(from_id)
    to_name = SchoolClass.objects.filter(id=to_id).values_list('name', flat=True).first() or str(to_id)
    count = Student.objects.filter(
        school_class_id=from_id, deleted_at__isnull=True
    ).count()
    return {
        'promoted': [{'from': from_name, 'to': to_name, 'count': count}],
        'graduated': [],
        'classesCreated': [],
    }
