from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from students.models import Student
from .models import BankAccount


@receiver(pre_save, sender=Student)
def sync_transaction_class_name(sender, instance, **kwargs):
    """Update transaction class_name when a student's class changes."""
    if instance.pk and instance.school_class_id:
        try:
            old = sender.objects.get(pk=instance.pk)
            if old.school_class_id != instance.school_class_id:
                new_class_name = instance.school_class.name if instance.school_class else None
                from .models import Transaction
                Transaction.objects.filter(student=instance).exclude(
                    class_name=new_class_name
                ).update(class_name=new_class_name)
        except sender.DoesNotExist:
            pass


@receiver([post_save, post_delete], sender=BankAccount)
def invalidate_internal_accounts_cache(sender, **kwargs):
    from .views import _invalidate_internal_accounts_cache
    _invalidate_internal_accounts_cache()
