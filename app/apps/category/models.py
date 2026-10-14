import uuid

from django.db import models

from apps.fields import AutoSlugField
from apps.memberships.models import Plan


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=220)
    description = models.TextField(blank=True)
    slug = AutoSlugField(populate_from=("name", "id"), unique=True)
    tier = models.ForeignKey(
        Plan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Historical metadata only; episode access uses its explicit required_plan.",
    )
    weight = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["-weight", "name"]
        verbose_name_plural = "Categories"
