import uuid
from django.db import models


class Book(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    publication = models.CharField(max_length=255, blank=True, null=True)
    mrp = models.DecimalField(max_digits=12, decimal_places=2)
    discounted = models.DecimalField(max_digits=12, decimal_places=2)
    sell = models.DecimalField(max_digits=12, decimal_places=2)
    school_class = models.ForeignKey(
        'core.SchoolClass', on_delete=models.CASCADE,
        related_name='books'
    )

    def __str__(self):
        return f"{self.name} ({self.school_class.name})"
