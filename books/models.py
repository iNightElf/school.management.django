import uuid
from django.db import models


class Book(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    publication = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        verbose_name = 'Book'
        verbose_name_plural = 'Books'
        constraints = [
            models.CheckConstraint(condition=models.Q(mrp__gte=0), name='book_mrp_non_negative'),
            models.CheckConstraint(condition=models.Q(discounted__gte=0), name='book_discounted_non_negative'),
            models.CheckConstraint(condition=models.Q(sell__gte=0), name='book_sell_non_negative'),
        ]
    mrp = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discounted = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    sell = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    school_class = models.ForeignKey(
        'core.SchoolClass', on_delete=models.CASCADE,
        related_name='books'
    )

    def __str__(self):
        return f"{self.name} ({self.school_class.name})"
