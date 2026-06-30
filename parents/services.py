import json
import logging
from django.conf import settings
from .models import PushSubscription, NotificationLog

logger = logging.getLogger(__name__)

try:
    from pywebpush import webpush as _webpush, WebPushException
except ImportError:
    _webpush = None
    WebPushException = Exception


def notify(user, title, body, url=None, icon=None):
    subs = PushSubscription.objects.filter(user=user)
    if not subs.exists():
        return 0

    payload = json.dumps({
        'title': title,
        'body': body,
        'icon': icon or '/icon-192.svg',
        'data': {'url': url or '/'},
    })

    vapid_claims = {
        'sub': f'mailto:{settings.VAPID_CLAIM_EMAIL}',
    }
    sent = 0
    for sub in subs:
        try:
            _webpush(
                subscription_info={
                    'endpoint': sub.endpoint,
                    'keys': {'p256dh': sub.p256dh_key, 'auth': sub.auth_key},
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims=vapid_claims,
            )
            sent += 1
        except WebPushException as e:
            if hasattr(e, 'response') and e.response and e.response.status_code == 410:
                sub.delete()
            logger.warning('Push send failed for %s: %s', sub.endpoint[:50], e)
        except Exception as e:
            logger.error('Push error for %s: %s', sub.endpoint[:50], e)
    return sent


def notify_parents_of_student(student_id, event_type, title, body, url=None):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    parents = User.objects.filter(
        role='parent',
        parent_links__student_id=student_id,
    ).distinct()

    for parent in parents:
        sent = 0
        err = None
        try:
            sent = notify(parent, title, body, url)
        except Exception as e:
            err = str(e)
            logger.exception('Error notifying %s: %s', parent.email, e)
        NotificationLog.objects.create(
            user=parent,
            event_type=event_type,
            title=title,
            body=body,
            payload={'student_id': str(student_id), 'url': url},
            error=err,
        )
    return parents.count()


def notify_parents_of_class(class_id, event_type, title, body, url=None):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    from parents.models import ParentStudentLink
    parent_ids = ParentStudentLink.objects.filter(
        student__school_class_id=class_id,
    ).values_list('parent_id', flat=True).distinct()
    parents = User.objects.filter(id__in=parent_ids)

    count = 0
    for parent in parents:
        sent = 0
        err = None
        try:
            sent = notify(parent, title, body, url)
        except Exception as e:
            err = str(e)
            logger.exception('Error notifying %s: %s', parent.email, e)
        NotificationLog.objects.create(
            user=parent,
            event_type=event_type,
            title=title,
            body=body,
            payload={'class_id': str(class_id), 'url': url},
            error=err,
        )
        count += 1
    return count


def notify_all_parents(title, body, url=None, event_type='announcement'):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    parents = User.objects.filter(role='parent')

    count = 0
    for parent in parents:
        sent = 0
        err = None
        try:
            sent = notify(parent, title, body, url)
        except Exception as e:
            err = str(e)
            logger.exception('Error notifying %s: %s', parent.email, e)
        NotificationLog.objects.create(
            user=parent,
            event_type=event_type,
            title=title,
            body=body,
            payload={'url': url},
            error=err,
        )
        count += 1
    return count
