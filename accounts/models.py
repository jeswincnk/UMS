from django.conf import settings
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = (
        ('student', 'Student'),
        ('faculty', 'Faculty'),
        ('college', 'College'),
        ('admin', 'Admin'),
    )

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email


class StudentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    college = models.ForeignKey('College', null=True, blank=True, on_delete=models.SET_NULL, related_name='students')
    department = models.ForeignKey('academic.Department', null=True, blank=True, on_delete=models.SET_NULL)
    program = models.ForeignKey('academic.Program', null=True, blank=True, on_delete=models.SET_NULL)
    semester = models.IntegerField(null=True, blank=True, default=1)
    dob = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    roll_number = models.CharField(max_length=50, blank=True)
    admission_date = models.DateField(null=True, blank=True)

    @property
    def student_id(self):
        return f"STU{self.pk:04d}" if self.pk else None

    def __str__(self):
        return f"{self.student_id} - {self.user.email}"


class FacultyProfile(models.Model):
    DESIGNATION_CHOICES = (
        ('faculty', 'Faculty'),
        ('hod', 'Head of Department'),
        ('principal', 'Principal'),
    )
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='faculty_profile')
    college = models.ForeignKey('College', null=True, blank=True, on_delete=models.SET_NULL, related_name='faculty_members')
    departments = models.ManyToManyField('academic.Department', blank=True, related_name='faculty')
    designation = models.CharField(max_length=20, choices=DESIGNATION_CHOICES, default='faculty')
    qualification = models.CharField(max_length=256, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    specialization = models.CharField(max_length=256, blank=True)
    joining_date = models.DateField(null=True, blank=True)

    @property
    def faculty_id(self):
        return f"FAC{self.pk:04d}" if self.pk else None
    
    @property
    def is_hod(self):
        return self.designation == 'hod'
    
    @property
    def is_principal(self):
        return self.designation == 'principal'

    def __str__(self):
        return f"{self.faculty_id} - {self.user.email}"


class College(models.Model):
    """
    Represents a college that can affiliate with the university.
    Colleges must be approved by the university admin before they can
    select departments and enroll students.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    
    AFFILIATION_STATUS_CHOICES = (
        ('not_applied', 'Not Applied'),
        ('pending', 'Affiliation Pending'),
        ('approved', 'Affiliated'),
        ('rejected', 'Affiliation Rejected'),
    )
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='college_profile')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    established_year = models.IntegerField(null=True, blank=True)
    
    # Approval status (by university admin)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='approved_colleges'
    )
    rejection_reason = models.TextField(blank=True)
    
    # Affiliation status
    affiliation_status = models.CharField(max_length=20, choices=AFFILIATION_STATUS_CHOICES, default='not_applied')
    affiliation_applied_at = models.DateTimeField(null=True, blank=True)
    affiliation_approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def college_id(self):
        return f"COL{self.pk:04d}" if self.pk else None
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_affiliated(self):
        return self.affiliation_status == 'approved'
    
    @property
    def can_enroll_students(self):
        """College can enroll students only if approved and affiliated"""
        return self.is_approved and self.is_affiliated
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        ordering = ['name']


class CollegeAffiliatedDepartment(models.Model):
    """
    Tracks which departments a college has selected for affiliation.
    Colleges can only select departments after they are approved.
    """
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='affiliated_departments')
    department = models.ForeignKey('academic.Department', on_delete=models.CASCADE, related_name='affiliated_colleges')
    applied_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('college', 'department')
        verbose_name = 'College Affiliated Department'
        verbose_name_plural = 'College Affiliated Departments'
    
    def __str__(self):
        return f"{self.college.name} - {self.department.name}"


class CollegeAffiliatedProgram(models.Model):
    college = models.ForeignKey(College, on_delete=models.CASCADE, related_name='affiliated_programs')
    program = models.ForeignKey('academic.Program', on_delete=models.CASCADE, related_name='affiliated_colleges')

    class Meta:
        unique_together = ('college', 'program')

    def __str__(self):
        return f"{self.college.name} - {self.program.name}"
