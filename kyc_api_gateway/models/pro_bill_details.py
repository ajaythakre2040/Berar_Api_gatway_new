from django.db import models
from django.utils import timezone

class ProElectricityBill(models.Model):
    client_id = models.CharField(max_length=100, null=True, blank=True)
    consumer_id = models.CharField(max_length=100, null=True, blank=True)
    customer_id = models.CharField(max_length=100, null=True, blank=True)
    operator_code = models.CharField(max_length=50, null=True, blank=True)
    service_provider = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    district = models.CharField(max_length=100, null=True, blank=True)
    full_name = models.CharField(max_length=200, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    reg_mobile_no = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    bill_number = models.CharField(max_length=100, null=True, blank=True)
    bill_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    bill_due_date = models.CharField(max_length=50, null=True, blank=True)
    bill_issue_date = models.CharField(max_length=50, null=True, blank=True)
    bill_status = models.CharField(max_length=50, null=True, blank=True)
    document_link = models.TextField(null=True, blank=True)
    full_response = models.JSONField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    updated_by = models.IntegerField(null=True, blank=True)
    deleted_by = models.IntegerField(null=True, blank=True)
    created_by = models.IntegerField()

    class Meta:
        db_table = "pro_bill_details"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.full_name or 'Unknown'} - {self.consumer_id or self.customer_id}"
