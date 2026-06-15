from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from students.models import Student
from .models import BankAccount


@receiver(pre_save, sender=Student)
def sync_transaction_class_name(sender, instance, **kwargs):
    """Log class changes but do NOT mutate financial records (immutable)."""
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            if old.school_class_id != instance.school_class_id:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    "Student %s (%s) changed class from %s to %s. "
                    "Transaction class_name preserved on historical records.",
                    instance.id, instance.name,
                    old.school_class_id, instance.school_class_id,
                )
        except sender.DoesNotExist:
            pass


@receiver([post_save, post_delete], sender=BankAccount)
def invalidate_internal_accounts_cache(sender, **kwargs):
    from .views import _invalidate_internal_accounts_cache
    _invalidate_internal_accounts_cache()
