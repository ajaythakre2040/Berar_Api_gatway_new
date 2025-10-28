from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ProVoterDetail(models.Model):
    VENDOR_CHOICES = (
        ("karza", "Karza"),
        ("surepass", "Surepass"),
    )

    vendor = models.CharField(max_length=50, choices=VENDOR_CHOICES)
    client_id = models.CharField(max_length=100, null=True, blank=True)
    epic_no = models.CharField(max_length=50, null=True, blank=True)
    input_voter_id = models.CharField(max_length=50, null=True, blank=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    relation_name = models.CharField(max_length=255, null=True, blank=True)
    relation_type = models.CharField(max_length=50, null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    dob = models.CharField(max_length=20, null=True, blank=True)
    age = models.CharField(max_length=5, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    assembly_constituency = models.CharField(max_length=100, null=True, blank=True)
    assembly_constituency_number = models.CharField(max_length=20, null=True, blank=True)
    polling_station = models.CharField(max_length=255, null=True, blank=True)
    part_no = models.CharField(max_length=10, null=True, blank=True)
    part_name = models.CharField(max_length=255, null=True, blank=True)
    slno_in_part = models.CharField(max_length=10, null=True, blank=True)
    ps_lat_long = models.CharField(max_length=50, null=True, blank=True)
    name_v1 = models.CharField(max_length=255, null=True, blank=True)
    name_v2 = models.CharField(max_length=255, null=True, blank=True)
    name_v3 = models.CharField(max_length=255, null=True, blank=True)
    rln_name_v1 = models.CharField(max_length=255, null=True, blank=True)
    rln_name_v2 = models.CharField(max_length=255, null=True, blank=True)
    rln_name_v3 = models.CharField(max_length=255, null=True, blank=True)
    ps_name = models.CharField(max_length=255, null=True, blank=True)
    house_no = models.CharField(max_length=50, null=True, blank=True)
    last_update = models.CharField(max_length=50, null=True, blank=True)
    parliamentary_name = models.CharField(max_length=100, null=True, blank=True)
    parliamentary_number = models.CharField(max_length=10, null=True, blank=True)
    st_code = models.CharField(max_length=20, null=True, blank=True)
    voter_id = models.CharField(max_length=100, null=True, blank=True)  # custom id
    
    created_by = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pro_voter_detail"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name or 'Unknown'} | {self.vendor}"
