from django.db import models
from django.conf import settings


class Enrollment(models.Model):
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE)
    offering = models.ForeignKey('academic.CourseOffering', on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=32, default='enrolled')

    class Meta:
        unique_together = ('student', 'offering')

    def __str__(self):
        return f"{self.student} -> {self.offering}"


class Exam(models.Model):
    offering = models.ForeignKey('academic.CourseOffering', on_delete=models.CASCADE)
    exam_date = models.DateField()
    max_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100)

    def __str__(self):
        return f"Exam for {self.offering} on {self.exam_date}"


class Result(models.Model):
    enrollment = models.OneToOneField(Enrollment, on_delete=models.CASCADE)
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    grade = models.CharField(max_length=8, blank=True)

    def __str__(self):
        return f"Result: {self.enrollment} -> {self.grade}"
