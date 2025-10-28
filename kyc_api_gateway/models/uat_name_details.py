from django.db import models
from django.utils import timezone

class UatNameMatch(models.Model):
    client_id = models.CharField(max_length=100, null=True, blank=True)
    request_id = models.CharField(max_length=100, null=True, blank=True)
    name_1 = models.CharField(max_length=200, null=True, blank=True)
    name_2 = models.CharField(max_length=200, null=True, blank=True)
    match_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    match_status = models.BooleanField(null=True, blank=True)
    

    created_by = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "uat_name_match"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name_1} ↔ {self.name_2} ({'Matched' if self.match_status else 'Not Matched'})"
