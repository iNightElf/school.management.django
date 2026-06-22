import time
import logging

logger = logging.getLogger(__name__)


class ConversationMemory:
    _store = {}
    _timestamps = {}
    _ttl = 300

    def get(self, user_id):
        entry = self._store.get(user_id, {})
        if time.time() - self._timestamps.get(user_id, 0) > self._ttl:
            return {}
        return entry

    def set(self, user_id, data):
        self._store[user_id] = data
        self._timestamps[user_id] = time.time()

    def clear(self, user_id):
        self._store.pop(user_id, None)
        self._timestamps.pop(user_id, None)


memory = ConversationMemory()


def resolve_slots(func_name, args):
    resolved = dict(args)

    class_name = resolved.get('class_name')
    if class_name and isinstance(class_name, str) and not isinstance(class_name, int):
        from core.models import SchoolClass
        try:
            obj = SchoolClass.objects.filter(name__iexact=class_name).first()
            if obj:
                resolved['class_name'] = obj.name
            else:
                logger.info(f"Class not found: {class_name}")
        except Exception:
            pass

    student_id = resolved.get('student_id')
    if student_id and isinstance(student_id, str) and len(student_id) < 30:
        from students.models import Student
        try:
            obj = Student.objects.filter(student_id=student_id).first()
            if not obj:
                obj = Student.objects.filter(name__icontains=student_id).first()
            if obj:
                resolved['student_id'] = obj.student_id
        except Exception:
            pass

    return resolved
