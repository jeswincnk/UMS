from django.db import models
from django.conf import settings


class Department(models.Model):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    head = models.ForeignKey(
        'accounts.FacultyProfile',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='headed_departments'
    )

    def __str__(self):
        return self.name


class Program(models.Model):
    name = models.CharField(max_length=200)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='programs')
    duration_years = models.IntegerField(default=4)

    def __str__(self):
        return self.name


class Course(models.Model):
    code = models.CharField(max_length=20, unique=True)
    title = models.CharField(max_length=255)
    credits = models.DecimalField(max_digits=4, decimal_places=1, default=3.0)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.code} - {self.title}"


class CourseOffering(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    term = models.CharField(max_length=64)
    year = models.IntegerField()
    instructor = models.ForeignKey('accounts.FacultyProfile', null=True, blank=True, on_delete=models.SET_NULL)
    capacity = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"{self.course.code} ({self.term} {self.year})"


class ClassSlot(models.Model):
    offering = models.ForeignKey(CourseOffering, on_delete=models.CASCADE, related_name='slots')
    day = models.CharField(max_length=10)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, blank=True)

    def __str__(self):
        return f"{self.offering} - {self.day} {self.start_time}-{self.end_time}"


class ProgramSemesterCourse(models.Model):
    """Links courses to specific semesters within a program"""
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='semester_courses')
    semester = models.IntegerField()
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='program_semesters')
    is_elective = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('program', 'semester', 'course')
        ordering = ['program', 'semester', 'course__code']
    
    def __str__(self):
        return f"{self.program.name} - Sem {self.semester} - {self.course.code}"


# ============ EXAM NOTIFICATION MODELS ============

class ExamNotification(models.Model):
    """Exam notifications - College level or University level"""
    TYPE_CHOICES = (
        ('college', 'College Exam'),
        ('university', 'University Exam'),
    )
    
    PRIORITY_CHOICES = (
        ('normal', 'Normal'),
        ('important', 'Important'),
        ('urgent', 'Urgent'),
    )
    
    notification_type = models.CharField(max_length=16, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    content = models.TextField()
    priority = models.CharField(max_length=16, choices=PRIORITY_CHOICES, default='normal')
    
    # For college notifications
    college = models.ForeignKey('accounts.College', on_delete=models.CASCADE, null=True, blank=True, related_name='exam_notifications')
    
    # Created by (Faculty for college, Admin user for university)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_notifications')
    
    exam_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"[{self.get_notification_type_display()}] {self.title}"


# ============ UNIVERSITY EXAM & RESULTS MODELS ============

class UniversityExam(models.Model):
    """University examination"""
    name = models.CharField(max_length=255)  # e.g., "End Semester Exam - Dec 2025"
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='university_exams')
    semester = models.IntegerField()
    academic_year = models.CharField(max_length=20)  # e.g., "2025-2026"
    exam_start_date = models.DateField()
    exam_end_date = models.DateField()
    result_published = models.BooleanField(default=False)
    result_published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-exam_start_date']
    
    def __str__(self):
        return f"{self.name} - {self.program.name} Sem {self.semester}"


class ExamSubject(models.Model):
    """Subjects in an exam"""
    exam = models.ForeignKey(UniversityExam, on_delete=models.CASCADE, related_name='subjects')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exam_subjects')
    max_marks = models.IntegerField(default=100)
    pass_marks = models.IntegerField(default=40)
    exam_date = models.DateField(null=True, blank=True)
    
    class Meta:
        unique_together = ('exam', 'course')
    
    def __str__(self):
        return f"{self.exam.name} - {self.course.code}"


class StudentResult(models.Model):
    """Student results for each subject in an exam"""
    GRADE_CHOICES = (
        ('O', 'Outstanding'),
        ('A+', 'Excellent'),
        ('A', 'Very Good'),
        ('B+', 'Good'),
        ('B', 'Above Average'),
        ('C', 'Average'),
        ('P', 'Pass'),
        ('F', 'Fail'),
        ('AB', 'Absent'),
    )
    
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='exam_results')
    exam_subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE, related_name='results')
    marks_obtained = models.IntegerField(null=True, blank=True)
    grade = models.CharField(max_length=4, choices=GRADE_CHOICES, blank=True)
    is_pass = models.BooleanField(default=False)
    remarks = models.CharField(max_length=255, blank=True)
    entered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='entered_results')
    entered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('student', 'exam_subject')
    
    def save(self, *args, **kwargs):
        # Auto-calculate grade and pass status
        if self.marks_obtained is not None:
            max_marks = self.exam_subject.max_marks
            pass_marks = self.exam_subject.pass_marks
            percentage = (self.marks_obtained / max_marks) * 100
            
            self.is_pass = self.marks_obtained >= pass_marks
            
            # Grade calculation
            if percentage >= 90:
                self.grade = 'O'
            elif percentage >= 80:
                self.grade = 'A+'
            elif percentage >= 70:
                self.grade = 'A'
            elif percentage >= 60:
                self.grade = 'B+'
            elif percentage >= 55:
                self.grade = 'B'
            elif percentage >= 50:
                self.grade = 'C'
            elif percentage >= pass_marks:
                self.grade = 'P'
            else:
                self.grade = 'F'
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.exam_subject.course.code} - {self.marks_obtained}"


# ============ QUESTION PAPER MODELS ============

class QuestionPaper(models.Model):
    """Question papers uploaded by university admin"""
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('released', 'Released'),
    )
    
    exam_subject = models.ForeignKey(ExamSubject, on_delete=models.CASCADE, related_name='question_papers')
    title = models.CharField(max_length=255)
    paper_file = models.FileField(upload_to='question_papers/')
    release_datetime = models.DateTimeField()  # When to release to colleges
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='draft')
    
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='uploaded_question_papers')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
    
    # Track downloads
    download_count = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-release_datetime']
    
    def __str__(self):
        return f"{self.title} - {self.exam_subject.course.code}"


class QuestionPaperDownload(models.Model):
    """Track who downloaded question papers"""
    question_paper = models.ForeignKey(QuestionPaper, on_delete=models.CASCADE, related_name='downloads')
    college = models.ForeignKey('accounts.College', on_delete=models.CASCADE)
    downloaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    downloaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-downloaded_at']

