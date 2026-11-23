
from django.db import models


class Location(models.Model):
    location_code = models.CharField(max_length=50, unique=True, null=True, blank=True)
    org_id = models.CharField(max_length=50)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class SystemARecord(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    reference = models.CharField(max_length=100)
    event_date = models.DateField(null=True, blank=True)
    category_code = models.CharField(max_length=50, blank=True)
    actor_id = models.CharField(max_length=50, blank=True)
    base_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    adjustment = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    state = models.CharField(max_length=50, blank=True)
    original_data = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["location", "reference"],
                name="unique_system_a_record"
            )
        ]


class SystemBEntry(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    entry_id = models.CharField(max_length=100)
    reference = models.CharField(max_length=100)
    recorded_on = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    label = models.CharField(max_length=200, blank=True)
    original_data = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["location", "entry_id"],
                name="unique_system_b_entry"
            )
        ]
