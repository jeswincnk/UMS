from django.db import models
from django.conf import settings


class AttendanceRecord(models.Model):
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE)
    offering = models.ForeignKey('academic.CourseOffering', on_delete=models.CASCADE)
    date = models.DateField()
    status = models.CharField(max_length=16, choices=(('present','Present'),('absent','Absent')))

    class Meta:
        unique_together = ('student', 'offering', 'date')

    def __str__(self):
        return f"{self.date} - {self.student} - {self.status}"


class AttendanceSession(models.Model):
    """Attendance session for a subject on a specific date"""
    college = models.ForeignKey('accounts.College', on_delete=models.CASCADE, related_name='attendance_sessions')
    department = models.ForeignKey('academic.Department', on_delete=models.CASCADE, related_name='attendance_sessions')
    subject = models.ForeignKey('academic.Course', on_delete=models.CASCADE, related_name='attendance_sessions')
    program = models.ForeignKey('academic.Program', on_delete=models.CASCADE, related_name='attendance_sessions', null=True, blank=True)
    semester = models.IntegerField(default=1)
    date = models.DateField()
    created_by = models.ForeignKey('accounts.FacultyProfile', on_delete=models.SET_NULL, null=True, related_name='created_attendance_sessions')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('college', 'subject', 'date', 'semester')
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.subject.code} - {self.date} - Sem {self.semester}"


class StudentAttendance(models.Model):
    """Individual student attendance for a session"""
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('leave', 'Leave'),
    )
    
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='student_attendances')
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='attendances')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='present')
    remarks = models.CharField(max_length=255, blank=True)
    
    class Meta:
        unique_together = ('session', 'student')
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.session.date} - {self.status}"


class MedicalCertificate(models.Model):
    """Medical certificate submission for leave requests"""
    STATUS_CHOICES = (
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='medical_certificates')
    month = models.IntegerField()  # 1-12
    year = models.IntegerField()
    certificate_file = models.FileField(upload_to='medical_certificates/')
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='pending')
    reviewed_by = models.ForeignKey('accounts.FacultyProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_certificates')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('student', 'month', 'year')
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.month}/{self.year}"

