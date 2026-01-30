from django.db import models


class FeeRecord(models.Model):
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=32, default='pending')

    def __str__(self):
        return f"{self.student} - {self.amount} ({self.status})"
