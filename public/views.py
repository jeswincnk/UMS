from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from django.db.models.functions import TruncMonth
from datetime import datetime, date, timedelta
from academic.models import Course, Department, Program, ExamNotification, UniversityExam, ExamSubject, StudentResult, QuestionPaper, ProgramSemesterCourse
from accounts.models import College, CollegeAffiliatedDepartment, CollegeAffiliatedProgram, StudentProfile, FacultyProfile
from attendance.models import AttendanceSession, StudentAttendance, MedicalCertificate
import json
import calendar

User = get_user_model()


def college_required(view_func):
    """Decorator to ensure user is a college"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'college':
            messages.error(request, 'Access denied. This area is for colleges only.')
            return redirect('public:index')
        try:
            college_profile = request.user.college_profile
        except College.DoesNotExist:
            messages.error(request, 'College profile not found.')
            return redirect('public:index')
        return view_func(request, *args, **kwargs)
    return wrapper


def student_required(view_func):
    """Decorator to ensure user is a student"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'student':
            messages.error(request, 'Access denied. This area is for students only.')
            return redirect('public:index')
        try:
            student_profile = request.user.studentprofile
        except StudentProfile.DoesNotExist:
            messages.error(request, 'Student profile not found.')
            return redirect('public:index')
        return view_func(request, *args, **kwargs)
    return wrapper


def faculty_required(view_func):
    """Decorator to ensure user is a faculty member"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'faculty':
            messages.error(request, 'Access denied. This area is for faculty only.')
            return redirect('public:index')
        try:
            faculty_profile = request.user.faculty_profile
        except FacultyProfile.DoesNotExist:
            messages.error(request, 'Faculty profile not found.')
            return redirect('public:index')
        return view_func(request, *args, **kwargs)
    return wrapper


def hod_required(view_func):
    """Decorator to ensure user is an HOD"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'faculty':
            messages.error(request, 'Access denied. This area is for HODs only.')
            return redirect('public:index')
        try:
            faculty_profile = request.user.faculty_profile
            if faculty_profile.designation != 'hod':
                messages.error(request, 'Access denied. This area is for HODs only.')
                return redirect('public:index')
        except FacultyProfile.DoesNotExist:
            messages.error(request, 'Faculty profile not found.')
            return redirect('public:index')
        return view_func(request, *args, **kwargs)
    return wrapper


def principal_required(view_func):
    """Decorator to ensure user is a principal"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.role != 'faculty':
            messages.error(request, 'Access denied. This area is for Principals only.')
            return redirect('public:index')
        try:
            faculty_profile = request.user.faculty_profile
            if faculty_profile.designation != 'principal':
                messages.error(request, 'Access denied. This area is for Principals only.')
                return redirect('public:index')
        except FacultyProfile.DoesNotExist:
            messages.error(request, 'Faculty profile not found.')
            return redirect('public:index')
        return view_func(request, *args, **kwargs)
    return wrapper



def index(request):
    """Public homepage"""
    return render(request, 'public/index.html')


def about(request):
    """Public about page"""
    return render(request, 'public/about.html')


def courses(request):
    """Public courses listing page"""
    q = request.GET.get('q', '').strip()
    qs = Course.objects.select_related('department').all().order_by('code')
    
    if q:
        qs = qs.filter(
            Q(code__icontains=q) |
            Q(title__icontains=q) |
            Q(department__name__icontains=q)
        )
    
    # Get all departments for the sidebar
    departments = Department.objects.all().order_by('name')
    
    # Pagination
    paginator = Paginator(qs, 12)
    page = request.GET.get('page')
    try:
        courses_page = paginator.page(page)
    except PageNotAnInteger:
        courses_page = paginator.page(1)
    except EmptyPage:
        courses_page = paginator.page(paginator.num_pages)
    
    context = {
        'courses': courses_page,
        'departments': departments,
        'query': q,
    }
    return render(request, 'public/courses.html', context)


def contact(request):
    """Public contact page with form handling"""
    if request.method == 'POST':
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        subject = request.POST.get('subject', '')
        message_text = request.POST.get('message', '')
        
        # Basic validation
        if name and email and subject and message_text:
            # In a real app, you would save this to database or send email
            # For now, just show a success message
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return render(request, 'public/contact.html')


def college_register(request):
    """College registration page - colleges can register and await admin approval"""
    if request.method == 'POST':
        # College information
        college_name = request.POST.get('college_name', '').strip()
        college_code = request.POST.get('college_code', '').strip().upper()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        established_year = request.POST.get('established_year', '').strip()
        
        # Account information
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        confirm_password = request.POST.get('confirm_password', '').strip()
        
        # Validation
        errors = []
        
        if not college_name:
            errors.append('College name is required.')
        if not college_code:
            errors.append('College code is required.')
        if not email:
            errors.append('Email is required.')
        if not password:
            errors.append('Password is required.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        
        if User.objects.filter(email=email).exists():
            errors.append('An account with this email already exists.')
        if College.objects.filter(code=college_code).exists():
            errors.append('A college with this code already exists.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Create user account with college role
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=college_name,
                role='college'
            )
            
            # Create college profile with pending status
            college = College.objects.create(
                user=user,
                name=college_name,
                code=college_code,
                email=email,
                address=address,
                phone=phone,
                established_year=int(established_year) if established_year else None,
                status='pending'  # Awaiting admin approval
            )
            
            messages.success(
                request, 
                f'Registration successful! Your college "{college_name}" has been registered and is pending approval. '
                f'You will be notified once the university administration reviews your application.'
            )
            return redirect('public:college_register')
    
    return render(request, 'public/college_register.html')


# ========== COLLEGE PORTAL VIEWS ==========

@login_required
@college_required
def college_dashboard(request):
    """College dashboard - main landing page after login"""
    college = request.user.college_profile
    
    context = {
        'college': college,
        'affiliated_departments': college.affiliated_departments.select_related('department').all(),
        'departments_count': college.affiliated_departments.count(),
        'students_count': college.students.count(),
    }
    return render(request, 'public/college/dashboard.html', context)


@login_required
@college_required
def college_profile(request):
    """View and edit college profile"""
    college = request.user.college_profile
    
    if request.method == 'POST':
        # Allow editing basic profile info
        college.name = request.POST.get('name', college.name).strip()
        college.email = request.POST.get('email', college.email).strip()
        college.address = request.POST.get('address', '').strip()
        college.phone = request.POST.get('phone', '').strip()
        college.website = request.POST.get('website', '').strip()
        college.description = request.POST.get('description', '').strip()
        college.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('public:college_profile')
    
    context = {
        'college': college,
    }
    return render(request, 'public/college/profile.html', context)


@login_required
@college_required
def college_select_departments(request):
    """Select departments for affiliation"""
    college = request.user.college_profile
    
    # Check if college is approved
    if not college.is_approved:
        messages.warning(request, 'Your college registration is still pending approval. You cannot select departments yet.')
        return redirect('public:college_dashboard')
    
    all_departments = Department.objects.all().order_by('name')
    affiliated_dept_ids = list(college.affiliated_departments.values_list('department_id', flat=True))
    
    # Get affiliated program ids for the college
    affiliated_program_ids = list(college.affiliated_programs.values_list('program_id', flat=True))
    # Attach programs to each department for template
    departments_with_programs = []
    for dept in all_departments:
        programs = Program.objects.filter(department=dept).order_by('name')
        departments_with_programs.append({
            'department': dept,
            'programs': programs,
        })

    if request.method == 'POST':
        # Check if already affiliated - can't change departments after affiliation is approved
        if college.affiliation_status == 'approved':
            messages.warning(request, 'Your affiliation is already approved. You cannot modify departments.')
            return redirect('public:college_select_departments')
        
        selected_programs = request.POST.getlist('programs')
        
        # Clear existing and add new program selections
        college.affiliated_programs.all().delete()
        college.affiliated_departments.all().delete()
        
        dept_ids = set()
        for prog_id in selected_programs:
            prog = Program.objects.get(pk=prog_id)
            CollegeAffiliatedProgram.objects.create(
                college=college,
                program=prog
            )
            dept_ids.add(prog.department_id)
        
        # Save departments based on selected programs
        for dept_id in dept_ids:
            CollegeAffiliatedDepartment.objects.get_or_create(
                college=college,
                department_id=dept_id
            )
        
        if selected_programs:
            if college.affiliation_status == 'not_applied':
                college.affiliation_status = 'pending'
                college.affiliation_applied_at = timezone.now()
                college.save()
                messages.success(request, 'Programs selected and affiliation request submitted! Please wait for university approval.')
            else:
                messages.success(request, 'Programs updated successfully.')
        else:
            messages.info(request, 'No programs selected.')
        
        return redirect('public:college_select_departments')
    
    context = {
        'college': college,
        'departments': departments_with_programs,
        'selected_dept_ids': affiliated_dept_ids,
        'affiliated_program_ids': affiliated_program_ids,
    }
    return render(request, 'public/college/select_departments.html', context)


@login_required
@college_required
def college_students(request):
    """List students enrolled by this college"""
    college = request.user.college_profile
    
    # Check if college can enroll students
    if not college.can_enroll_students:
        messages.warning(request, 'Your college is not yet authorized to manage students. Complete registration and affiliation first.')
        return redirect('public:college_dashboard')
    
    q = request.GET.get('q', '').strip()
    students = college.students.select_related('user', 'department', 'program').all().order_by('-pk')
    
    if q:
        students = students.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(user__email__icontains=q) |
            Q(roll_number__icontains=q)
        )
    
    # Get programs from affiliated departments
    affiliated_departments = college.affiliated_departments.select_related('department').all()
    affiliated_dept_ids = list(affiliated_departments.values_list('department_id', flat=True))
    available_programs = Program.objects.filter(department_id__in=affiliated_dept_ids).order_by('name')
    
    paginator = Paginator(students, 10)
    page = request.GET.get('page')
    try:
        students_page = paginator.page(page)
    except PageNotAnInteger:
        students_page = paginator.page(1)
    except EmptyPage:
        students_page = paginator.page(paginator.num_pages)
    
    context = {
        'college': college,
        'students': students_page,
        'query': q,
        'available_programs': available_programs,
        'departments_count': len(affiliated_dept_ids),
        'programs_count': available_programs.count(),
    }
    return render(request, 'public/college/students.html', context)


@login_required
@college_required
def college_add_student(request):
    """Add a new student to the college"""
    import json
    college = request.user.college_profile
    
    # Check if college can enroll students
    if not college.can_enroll_students:
        messages.warning(request, 'Your college is not yet authorized to enroll students.')
        return redirect('public:college_dashboard')
    
    # Get affiliated departments with programs
    affiliated_departments = college.affiliated_departments.select_related('department').all()
    
    # Build a map of department_id -> affiliated programs for this college
    affiliated_programs = college.affiliated_programs.select_related('program', 'program__department').all()
    dept_programs_map = {}
    for ap in affiliated_programs:
        dept_id = ap.program.department_id
        if dept_id not in dept_programs_map:
            dept_programs_map[dept_id] = []
        dept_programs_map[dept_id].append({
            'id': ap.program.id,
            'name': ap.program.name
        })
    dept_programs_json = json.dumps(dept_programs_map)
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        department_id = request.POST.get('department', '').strip()
        program_id = request.POST.get('program', '').strip()
        roll_number = request.POST.get('roll_number', '').strip()
        admission_date = request.POST.get('admission_date', '').strip() or None
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()
        
        # Validation
        errors = []
        if not email:
            errors.append('Email is required.')
        if not first_name:
            errors.append('First name is required.')
        if not last_name:
            errors.append('Last name is required.')
        if not password:
            errors.append('Password is required.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != password_confirm:
            errors.append('Passwords do not match.')
        if User.objects.filter(email=email).exists():
            errors.append('A user with this email already exists.')
        if not department_id:
            errors.append('Department is required.')
        if not program_id:
            errors.append('Program is required.')
        
        # Validate that the selected program is affiliated with this college
        if program_id and not college.affiliated_programs.filter(program_id=program_id).exists():
            errors.append('Selected program is not affiliated with your college.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Create user
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='student'
            )
            
            # Get department and program
            department = Department.objects.get(pk=department_id)
            program = Program.objects.get(pk=program_id)
            
            # Create student profile
            student = StudentProfile.objects.create(
                user=user,
                college=college,
                department=department,
                program=program,
                roll_number=roll_number,
                phone=phone,
            )
            
            messages.success(request, f'Student {first_name} {last_name} enrolled successfully!')
            return redirect('public:college_students')
    
    context = {
        'college': college,
        'departments': affiliated_departments,
        'dept_programs_json': dept_programs_json,
    }
    return render(request, 'public/college/add_student.html', context)


@login_required
@college_required
def college_view_student(request, student_id):
    """View a student's details"""
    college = request.user.college_profile
    
    # Get the student, ensuring they belong to this college
    student = get_object_or_404(StudentProfile, pk=student_id, college=college)
    
    context = {
        'college': college,
        'student': student,
    }
    return render(request, 'public/college/view_student.html', context)


@login_required
@college_required
def college_edit_student(request, student_id):
    """Edit a student's details"""
    import json
    college = request.user.college_profile
    
    # Get the student, ensuring they belong to this college
    student = get_object_or_404(StudentProfile, pk=student_id, college=college)
    
    # Get affiliated departments with programs
    affiliated_departments = college.affiliated_departments.select_related('department').all()
    
    # Build a map of department_id -> affiliated programs for this college
    affiliated_programs = college.affiliated_programs.select_related('program', 'program__department').all()
    dept_programs_map = {}
    for ap in affiliated_programs:
        dept_id = ap.program.department_id
        if dept_id not in dept_programs_map:
            dept_programs_map[dept_id] = []
        dept_programs_map[dept_id].append({
            'id': ap.program.id,
            'name': ap.program.name
        })
    dept_programs_json = json.dumps(dept_programs_map)
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        department_id = request.POST.get('department', '').strip()
        program_id = request.POST.get('program', '').strip()
        roll_number = request.POST.get('roll_number', '').strip()
        admission_date = request.POST.get('admission_date', '').strip() or None
        
        # Validation
        errors = []
        if not first_name:
            errors.append('First name is required.')
        if not last_name:
            errors.append('Last name is required.')
        if not department_id:
            errors.append('Department is required.')
        if not program_id:
            errors.append('Program is required.')
        
        # Validate that the selected program is affiliated with this college
        if program_id and not college.affiliated_programs.filter(program_id=program_id).exists():
            errors.append('Selected program is not affiliated with your college.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Update user info
            student.user.first_name = first_name
            student.user.last_name = last_name
            student.user.save()
            
            # Update student profile
            student.department = Department.objects.get(pk=department_id)
            student.program = Program.objects.get(pk=program_id)
            student.roll_number = roll_number
            student.phone = phone
            if admission_date:
                student.admission_date = admission_date
            student.save()
            
            messages.success(request, f'Student {first_name} {last_name} updated successfully!')
            return redirect('public:college_students')
    
    context = {
        'college': college,
        'student': student,
        'departments': affiliated_departments,
        'dept_programs_json': dept_programs_json,
    }
    return render(request, 'public/college/edit_student.html', context)


# ========== COLLEGE FACULTY MANAGEMENT ==========

@login_required
@college_required
def college_faculty(request):
    """List faculty members of this college"""
    college = request.user.college_profile
    
    if not college.can_enroll_students:
        messages.warning(request, 'Your college is not yet authorized to manage faculty. Complete registration and affiliation first.')
        return redirect('public:college_dashboard')
    
    q = request.GET.get('q', '').strip()
    designation_filter = request.GET.get('designation', '').strip()
    
    faculty_list = college.faculty_members.select_related('user').prefetch_related('departments').all().order_by('-pk')
    
    if q:
        faculty_list = faculty_list.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(user__email__icontains=q)
        )
    
    if designation_filter:
        faculty_list = faculty_list.filter(designation=designation_filter)
    
    # Get affiliated departments
    affiliated_departments = college.affiliated_departments.select_related('department').all()
    
    paginator = Paginator(faculty_list, 10)
    page = request.GET.get('page')
    try:
        faculty_page = paginator.page(page)
    except PageNotAnInteger:
        faculty_page = paginator.page(1)
    except EmptyPage:
        faculty_page = paginator.page(paginator.num_pages)
    
    context = {
        'college': college,
        'faculty_list': faculty_page,
        'query': q,
        'designation_filter': designation_filter,
        'departments_count': affiliated_departments.count(),
        'faculty_count': college.faculty_members.filter(designation='faculty').count(),
        'hod_count': college.faculty_members.filter(designation='hod').count(),
        'principal_count': college.faculty_members.filter(designation='principal').count(),
    }
    return render(request, 'public/college/faculty.html', context)


@login_required
@college_required
def college_add_faculty(request):
    """Add a new faculty member to the college"""
    college = request.user.college_profile
    
    if not college.can_enroll_students:
        messages.warning(request, 'Your college is not yet authorized to add faculty.')
        return redirect('public:college_dashboard')
    
    # Get affiliated departments
    affiliated_departments = college.affiliated_departments.select_related('department').all()
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        designation = request.POST.get('designation', 'faculty').strip()
        qualification = request.POST.get('qualification', '').strip()
        specialization = request.POST.get('specialization', '').strip()
        joining_date = request.POST.get('joining_date', '').strip() or None
        department_ids = request.POST.getlist('departments')
        password = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()
        
        # Validation
        errors = []
        if not email:
            errors.append('Email is required.')
        if not first_name:
            errors.append('First name is required.')
        if not last_name:
            errors.append('Last name is required.')
        if not password:
            errors.append('Password is required.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if password != password_confirm:
            errors.append('Passwords do not match.')
        if User.objects.filter(email=email).exists():
            errors.append('A user with this email already exists.')
        if not department_ids:
            errors.append('At least one department is required.')
        
        # Validate departments are affiliated
        affiliated_dept_ids = list(affiliated_departments.values_list('department_id', flat=True))
        for dept_id in department_ids:
            if int(dept_id) not in affiliated_dept_ids:
                errors.append('One or more selected departments are not affiliated with your college.')
                break
        
        # Validate only one principal per college
        if designation == 'principal' and college.faculty_members.filter(designation='principal').exists():
            errors.append('This college already has a Principal. There can only be one Principal per college.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Create user
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='faculty'
            )
            
            # Create faculty profile
            faculty = FacultyProfile.objects.create(
                user=user,
                college=college,
                designation=designation,
                qualification=qualification,
                specialization=specialization,
                phone=phone,
                joining_date=joining_date,
            )
            
            # Add departments
            for dept_id in department_ids:
                faculty.departments.add(Department.objects.get(pk=dept_id))
            
            messages.success(request, f'{dict(FacultyProfile.DESIGNATION_CHOICES)[designation]} {first_name} {last_name} added successfully!')
            return redirect('public:college_faculty')
    
    context = {
        'college': college,
        'departments': affiliated_departments,
        'designation_choices': FacultyProfile.DESIGNATION_CHOICES,
    }
    return render(request, 'public/college/add_faculty.html', context)


@login_required
@college_required
def college_view_faculty(request, faculty_id):
    """View a faculty member's details"""
    college = request.user.college_profile
    
    faculty = get_object_or_404(FacultyProfile, pk=faculty_id, college=college)
    
    context = {
        'college': college,
        'faculty': faculty,
    }
    return render(request, 'public/college/view_faculty.html', context)


@login_required
@college_required
def college_edit_faculty(request, faculty_id):
    """Edit a faculty member's details"""
    college = request.user.college_profile
    
    faculty = get_object_or_404(FacultyProfile, pk=faculty_id, college=college)
    affiliated_departments = college.affiliated_departments.select_related('department').all()
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        designation = request.POST.get('designation', 'faculty').strip()
        qualification = request.POST.get('qualification', '').strip()
        specialization = request.POST.get('specialization', '').strip()
        joining_date = request.POST.get('joining_date', '').strip() or None
        department_ids = request.POST.getlist('departments')
        
        # Validation
        errors = []
        if not first_name:
            errors.append('First name is required.')
        if not last_name:
            errors.append('Last name is required.')
        if not department_ids:
            errors.append('At least one department is required.')
        
        # Validate only one principal per college (excluding current faculty)
        if designation == 'principal' and college.faculty_members.filter(designation='principal').exclude(pk=faculty_id).exists():
            errors.append('This college already has a Principal.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Update user info
            faculty.user.first_name = first_name
            faculty.user.last_name = last_name
            faculty.user.save()
            
            # Update faculty profile
            faculty.designation = designation
            faculty.qualification = qualification
            faculty.specialization = specialization
            faculty.phone = phone
            if joining_date:
                faculty.joining_date = joining_date
            faculty.save()
            
            # Update departments
            faculty.departments.clear()
            for dept_id in department_ids:
                faculty.departments.add(Department.objects.get(pk=dept_id))
            
            messages.success(request, f'{first_name} {last_name} updated successfully!')
            return redirect('public:college_faculty')
    
    context = {
        'college': college,
        'faculty': faculty,
        'departments': affiliated_departments,
        'designation_choices': FacultyProfile.DESIGNATION_CHOICES,
    }
    return render(request, 'public/college/edit_faculty.html', context)


# ========== STUDENT PORTAL ==========

@login_required
@student_required
def student_dashboard(request):
    """Student dashboard - main landing page after login"""
    student = request.user.studentprofile
    
    context = {
        'student': student,
        'college': student.college,
    }
    return render(request, 'public/student/dashboard.html', context)


@login_required
@student_required
def student_profile(request):
    """View and edit student profile"""
    student = request.user.studentprofile
    
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        student.phone = phone
        student.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('public:student_profile')
    
    context = {
        'student': student,
        'college': student.college,
    }
    return render(request, 'public/student/profile.html', context)


# ========== FACULTY PORTAL ==========

@login_required
@faculty_required
def faculty_dashboard(request):
    """Faculty dashboard - main landing page after login"""
    faculty = request.user.faculty_profile
    
    # Redirect to specific portal based on designation
    if faculty.designation == 'principal':
        return redirect('public:principal_dashboard')
    elif faculty.designation == 'hod':
        return redirect('public:hod_dashboard')
    
    context = {
        'faculty': faculty,
        'college': faculty.college,
        'departments': faculty.departments.all(),
    }
    return render(request, 'public/faculty/dashboard.html', context)


@login_required
@faculty_required
def faculty_profile(request):
    """View and edit faculty profile"""
    faculty = request.user.faculty_profile
    
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        specialization = request.POST.get('specialization', '').strip()
        faculty.phone = phone
        faculty.specialization = specialization
        faculty.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('public:faculty_profile')
    
    context = {
        'faculty': faculty,
        'college': faculty.college,
    }
    return render(request, 'public/faculty/profile.html', context)


# ========== HOD PORTAL ==========

@login_required
@hod_required
def hod_dashboard(request):
    """HOD dashboard - department management"""
    faculty = request.user.faculty_profile
    departments = faculty.departments.all()
    
    # Get stats for HOD's departments
    total_faculty = 0
    total_students = 0
    for dept in departments:
        total_faculty += FacultyProfile.objects.filter(departments=dept, college=faculty.college).count()
        total_students += StudentProfile.objects.filter(department=dept, college=faculty.college).count()
    
    context = {
        'faculty': faculty,
        'college': faculty.college,
        'departments': departments,
        'total_faculty': total_faculty,
        'total_students': total_students,
    }
    return render(request, 'public/hod/dashboard.html', context)


@login_required
@hod_required
def hod_profile(request):
    """HOD profile view"""
    faculty = request.user.faculty_profile
    
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        specialization = request.POST.get('specialization', '').strip()
        faculty.phone = phone
        faculty.specialization = specialization
        faculty.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('public:hod_profile')
    
    context = {
        'faculty': faculty,
        'college': faculty.college,
    }
    return render(request, 'public/hod/profile.html', context)


@login_required
@hod_required
def hod_faculty(request):
    """HOD view - manage faculty in their department"""
    faculty = request.user.faculty_profile
    departments = faculty.departments.all()
    
    # Get faculty in HOD's departments
    dept_faculty = FacultyProfile.objects.filter(
        departments__in=departments, 
        college=faculty.college
    ).distinct().select_related('user').prefetch_related('departments')
    
    context = {
        'faculty': faculty,
        'college': faculty.college,
        'departments': departments,
        'dept_faculty': dept_faculty,
    }
    return render(request, 'public/hod/faculty.html', context)


@login_required
@hod_required
def hod_students(request):
    """HOD view - view students in their department"""
    faculty = request.user.faculty_profile
    departments = faculty.departments.all()
    
    # Get students in HOD's departments
    dept_students = StudentProfile.objects.filter(
        department__in=departments,
        college=faculty.college
    ).select_related('user', 'department', 'program')
    
    context = {
        'faculty': faculty,
        'college': faculty.college,
        'departments': departments,
        'dept_students': dept_students,
    }
    return render(request, 'public/hod/students.html', context)


# ========== PRINCIPAL PORTAL ==========

@login_required
@principal_required
def principal_dashboard(request):
    """Principal dashboard - college overview"""
    faculty = request.user.faculty_profile
    college = faculty.college
    
    # Get college stats
    total_faculty = college.faculty_members.count()
    total_students = college.students.count()
    total_departments = college.affiliated_departments.count()
    total_hods = college.faculty_members.filter(designation='hod').count()
    
    context = {
        'faculty': faculty,
        'college': college,
        'total_faculty': total_faculty,
        'total_students': total_students,
        'total_departments': total_departments,
        'total_hods': total_hods,
    }
    return render(request, 'public/principal/dashboard.html', context)


@login_required
@principal_required
def principal_profile(request):
    """Principal profile view"""
    faculty = request.user.faculty_profile
    
    if request.method == 'POST':
        phone = request.POST.get('phone', '').strip()
        specialization = request.POST.get('specialization', '').strip()
        faculty.phone = phone
        faculty.specialization = specialization
        faculty.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('public:principal_profile')
    
    context = {
        'faculty': faculty,
        'college': faculty.college,
    }
    return render(request, 'public/principal/profile.html', context)


@login_required
@principal_required
def principal_faculty(request):
    """Principal view - all faculty in college"""
    faculty = request.user.faculty_profile
    college = faculty.college
    
    all_faculty = college.faculty_members.select_related('user').prefetch_related('departments').all()
    
    context = {
        'faculty': faculty,
        'college': college,
        'all_faculty': all_faculty,
    }
    return render(request, 'public/principal/faculty.html', context)


@login_required
@principal_required
def principal_students(request):
    """Principal view - all students in college"""
    faculty = request.user.faculty_profile
    college = faculty.college
    
    all_students = college.students.select_related('user', 'department', 'program').all()
    
    context = {
        'faculty': faculty,
        'college': college,
        'all_students': all_students,
    }
    return render(request, 'public/principal/students.html', context)


@login_required
@principal_required
def principal_departments(request):
    """Principal view - all departments in college"""
    faculty = request.user.faculty_profile
    college = faculty.college
    
    departments = college.affiliated_departments.select_related('department').all()
    
    # Add stats to each department
    dept_data = []
    for dept in departments:
        faculty_count = FacultyProfile.objects.filter(departments=dept.department, college=college).count()
        student_count = StudentProfile.objects.filter(department=dept.department, college=college).count()
        hod = FacultyProfile.objects.filter(
            departments=dept.department, 
            college=college, 
            designation='hod'
        ).first()
        dept_data.append({
            'department': dept.department,
            'faculty_count': faculty_count,
            'student_count': student_count,
            'hod': hod,
        })
    
    context = {
        'faculty': faculty,
        'college': college,
        'dept_data': dept_data,
    }
    return render(request, 'public/principal/departments.html', context)


# ============================================================
# ATTENDANCE MANAGEMENT VIEWS
# ============================================================

@login_required
@hod_required
def hod_attendance(request):
    """HOD view - Attendance management for their departments"""
    faculty = request.user.faculty_profile
    college = faculty.college
    departments = faculty.departments.all()
    
    # Get subjects (courses) for their departments
    dept_ids = list(departments.values_list('id', flat=True))
    subjects = Course.objects.filter(department_id__in=dept_ids)
    
    # Get recent attendance sessions
    sessions = AttendanceSession.objects.filter(
        college=college,
        department__in=departments
    ).select_related('subject', 'department', 'created_by__user')[:20]
    
    context = {
        'faculty': faculty,
        'college': college,
        'departments': departments,
        'subjects': subjects,
        'sessions': sessions,
    }
    return render(request, 'public/hod/attendance.html', context)


@login_required
@hod_required
def hod_add_attendance(request):
    """HOD adds attendance for a class"""
    faculty = request.user.faculty_profile
    college = faculty.college
    departments = faculty.departments.all()
    
    # Get subjects for their departments
    dept_ids = list(departments.values_list('id', flat=True))
    subjects = Course.objects.filter(department_id__in=dept_ids)
    programs = Program.objects.filter(department_id__in=dept_ids)
    
    if request.method == 'POST':
        department_id = request.POST.get('department')
        subject_id = request.POST.get('subject')
        program_id = request.POST.get('program')
        semester = request.POST.get('semester', 1)
        attendance_date = request.POST.get('date')
        
        # Validate
        if not all([department_id, subject_id, attendance_date]):
            messages.error(request, 'Please fill all required fields.')
        else:
            department = Department.objects.get(pk=department_id)
            subject = Course.objects.get(pk=subject_id)
            program = Program.objects.get(pk=program_id) if program_id else None
            
            # Check if session already exists
            existing = AttendanceSession.objects.filter(
                college=college,
                subject=subject,
                date=attendance_date,
                semester=semester
            ).first()
            
            if existing:
                messages.warning(request, 'Attendance session already exists for this subject and date.')
                return redirect('public:hod_edit_attendance', session_id=existing.pk)
            
            # Create session
            session = AttendanceSession.objects.create(
                college=college,
                department=department,
                subject=subject,
                program=program,
                semester=int(semester),
                date=attendance_date,
                created_by=faculty
            )
            
            messages.success(request, 'Attendance session created. Now mark attendance.')
            return redirect('public:hod_mark_attendance', session_id=session.pk)
    
    context = {
        'faculty': faculty,
        'college': college,
        'departments': departments,
        'subjects': subjects,
        'programs': programs,
        'today': date.today().isoformat(),
    }
    return render(request, 'public/hod/add_attendance.html', context)


@login_required
@hod_required
def hod_mark_attendance(request, session_id):
    """HOD marks attendance for students in a session"""
    faculty = request.user.faculty_profile
    college = faculty.college
    
    session = get_object_or_404(AttendanceSession, pk=session_id, college=college)
    
    # Get students for this program/department
    students = StudentProfile.objects.filter(
        college=college,
        department=session.department
    )
    if session.program:
        students = students.filter(program=session.program)
    students = students.select_related('user')
    
    # Get existing attendance records
    existing_attendance = {
        sa.student_id: sa for sa in session.student_attendances.all()
    }
    
    if request.method == 'POST':
        for student in students:
            status = request.POST.get(f'status_{student.pk}', 'present')
            remarks = request.POST.get(f'remarks_{student.pk}', '')
            
            if student.pk in existing_attendance:
                att = existing_attendance[student.pk]
                att.status = status
                att.remarks = remarks
                att.save()
            else:
                StudentAttendance.objects.create(
                    session=session,
                    student=student,
                    status=status,
                    remarks=remarks
                )
        
        messages.success(request, 'Attendance marked successfully!')
        return redirect('public:hod_attendance')
    
    context = {
        'faculty': faculty,
        'college': college,
        'session': session,
        'students': students,
        'existing_attendance': existing_attendance,
    }
    return render(request, 'public/hod/mark_attendance.html', context)


@login_required
@hod_required
def hod_edit_attendance(request, session_id):
    """HOD edits an existing attendance session"""
    return hod_mark_attendance(request, session_id)


@login_required
@hod_required
def hod_medical_certificates(request):
    """HOD reviews medical certificates from students"""
    faculty = request.user.faculty_profile
    college = faculty.college
    departments = faculty.departments.all()
    
    certificates = MedicalCertificate.objects.filter(
        student__college=college,
        student__department__in=departments
    ).select_related('student__user', 'student__department')
    
    context = {
        'faculty': faculty,
        'college': college,
        'certificates': certificates,
    }
    return render(request, 'public/hod/medical_certificates.html', context)


@login_required
@hod_required
def hod_review_certificate(request, cert_id):
    """HOD approves/rejects a medical certificate"""
    faculty = request.user.faculty_profile
    college = faculty.college
    
    certificate = get_object_or_404(MedicalCertificate, pk=cert_id, student__college=college)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            certificate.status = 'approved'
            certificate.reviewed_by = faculty
            certificate.reviewed_at = timezone.now()
            certificate.save()
            messages.success(request, 'Certificate approved.')
        elif action == 'reject':
            reason = request.POST.get('rejection_reason', '')
            certificate.status = 'rejected'
            certificate.reviewed_by = faculty
            certificate.reviewed_at = timezone.now()
            certificate.rejection_reason = reason
            certificate.save()
            messages.success(request, 'Certificate rejected.')
        
        return redirect('public:hod_medical_certificates')
    
    context = {
        'faculty': faculty,
        'college': college,
        'certificate': certificate,
    }
    return render(request, 'public/hod/review_certificate.html', context)


# ========== FACULTY ATTENDANCE ==========

@login_required
@faculty_required
def faculty_attendance(request):
    """Faculty view - Their subject attendance"""
    faculty = request.user.faculty_profile
    college = faculty.college
    departments = faculty.departments.all()
    
    # Get attendance sessions for subjects in their departments
    dept_ids = list(departments.values_list('id', flat=True))
    sessions = AttendanceSession.objects.filter(
        college=college,
        department_id__in=dept_ids
    ).select_related('subject', 'department', 'created_by__user')[:30]
    
    context = {
        'faculty': faculty,
        'college': college,
        'sessions': sessions,
    }
    return render(request, 'public/faculty/attendance.html', context)


@login_required
@faculty_required
def faculty_edit_attendance(request, session_id):
    """Faculty edits attendance for their subject"""
    faculty = request.user.faculty_profile
    college = faculty.college
    
    session = get_object_or_404(AttendanceSession, pk=session_id, college=college)
    
    # Check if faculty can edit (is in the department)
    if session.department not in faculty.departments.all():
        messages.error(request, 'You can only edit attendance for your department subjects.')
        return redirect('public:faculty_attendance')
    
    # Get students
    students = StudentProfile.objects.filter(
        college=college,
        department=session.department
    )
    if session.program:
        students = students.filter(program=session.program)
    students = students.select_related('user')
    
    existing_attendance = {
        sa.student_id: sa for sa in session.student_attendances.all()
    }
    
    if request.method == 'POST':
        for student in students:
            status = request.POST.get(f'status_{student.pk}', 'present')
            remarks = request.POST.get(f'remarks_{student.pk}', '')
            
            if student.pk in existing_attendance:
                att = existing_attendance[student.pk]
                att.status = status
                att.remarks = remarks
                att.save()
            else:
                StudentAttendance.objects.create(
                    session=session,
                    student=student,
                    status=status,
                    remarks=remarks
                )
        
        messages.success(request, 'Attendance updated successfully!')
        return redirect('public:faculty_attendance')
    
    context = {
        'faculty': faculty,
        'college': college,
        'session': session,
        'students': students,
        'existing_attendance': existing_attendance,
    }
    return render(request, 'public/faculty/edit_attendance.html', context)


# ========== STUDENT ATTENDANCE ==========

@login_required
@student_required
def student_attendance(request):
    """Student views their attendance"""
    student = request.user.studentprofile
    college = student.college
    
    # Get all attendance records for this student
    attendances = StudentAttendance.objects.filter(
        student=student
    ).select_related('session__subject', 'session__department')
    
    # Calculate monthly stats
    current_month = date.today().month
    current_year = date.today().year
    
    month_leaves = attendances.filter(
        session__date__month=current_month,
        session__date__year=current_year,
        status='leave'
    ).count()
    
    # Check if student needs to submit medical certificate (>3 leaves)
    needs_certificate = month_leaves > 3
    
    # Check if certificate already submitted
    existing_cert = MedicalCertificate.objects.filter(
        student=student,
        month=current_month,
        year=current_year
    ).first()
    
    # Subject-wise attendance summary
    subject_stats = {}
    for att in attendances:
        subj = att.session.subject.code
        if subj not in subject_stats:
            subject_stats[subj] = {'present': 0, 'absent': 0, 'leave': 0, 'total': 0, 'name': att.session.subject.title}
        subject_stats[subj][att.status] += 1
        subject_stats[subj]['total'] += 1
    
    # Calculate percentages
    for subj in subject_stats:
        total = subject_stats[subj]['total']
        present = subject_stats[subj]['present']
        subject_stats[subj]['percentage'] = round((present / total) * 100, 1) if total > 0 else 0
    
    context = {
        'student': student,
        'college': college,
        'attendances': attendances[:50],
        'month_leaves': month_leaves,
        'needs_certificate': needs_certificate,
        'existing_cert': existing_cert,
        'subject_stats': subject_stats,
        'current_month': calendar.month_name[current_month],
        'current_year': current_year,
    }
    return render(request, 'public/student/attendance.html', context)


@login_required
@student_required
def student_submit_medical_certificate(request):
    """Student submits medical certificate"""
    student = request.user.studentprofile
    
    current_month = date.today().month
    current_year = date.today().year
    
    # Check if already submitted
    existing = MedicalCertificate.objects.filter(
        student=student,
        month=current_month,
        year=current_year
    ).first()
    
    if existing:
        messages.warning(request, 'You have already submitted a certificate for this month.')
        return redirect('public:student_attendance')
    
    if request.method == 'POST':
        certificate_file = request.FILES.get('certificate')
        reason = request.POST.get('reason', '')
        
        if not certificate_file:
            messages.error(request, 'Please upload a certificate file.')
        else:
            MedicalCertificate.objects.create(
                student=student,
                month=current_month,
                year=current_year,
                certificate_file=certificate_file,
                reason=reason
            )
            messages.success(request, 'Medical certificate submitted successfully. Pending HOD review.')
            return redirect('public:student_attendance')
    
    context = {
        'student': student,
        'college': student.college,
        'current_month': calendar.month_name[current_month],
        'current_year': current_year,
    }
    return render(request, 'public/student/submit_certificate.html', context)


# ============================================================
# EXAM NOTIFICATION VIEWS
# ============================================================

@login_required
@hod_required
def hod_notifications(request):
    """HOD manages college exam notifications"""
    faculty = request.user.faculty_profile
    college = faculty.college
    
    # Get college notifications
    notifications = ExamNotification.objects.filter(college=college)
    
    # Get university notifications
    university_notifications = ExamNotification.objects.filter(
        notification_type='university',
        is_active=True
    )[:10]
    
    context = {
        'faculty': faculty,
        'college': college,
        'notifications': notifications,
        'university_notifications': university_notifications,
    }
    return render(request, 'public/hod/notifications.html', context)


@login_required
@hod_required
def hod_add_notification(request):
    """HOD adds a college exam notification"""
    faculty = request.user.faculty_profile
    college = faculty.college
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        priority = request.POST.get('priority', 'normal')
        exam_date = request.POST.get('exam_date') or None
        
        if not title or not content:
            messages.error(request, 'Title and content are required.')
        else:
            ExamNotification.objects.create(
                notification_type='college',
                title=title,
                content=content,
                priority=priority,
                college=college,
                created_by=request.user,
                exam_date=exam_date
            )
            messages.success(request, 'Notification created successfully!')
            return redirect('public:hod_notifications')
    
    context = {
        'faculty': faculty,
        'college': college,
    }
    return render(request, 'public/hod/add_notification.html', context)


@login_required
@student_required
def student_notifications(request):
    """Student views exam notifications"""
    student = request.user.studentprofile
    college = student.college
    
    # College notifications
    college_notifications = ExamNotification.objects.filter(
        college=college,
        notification_type='college',
        is_active=True
    )
    
    # University notifications
    university_notifications = ExamNotification.objects.filter(
        notification_type='university',
        is_active=True
    )
    
    context = {
        'student': student,
        'college': college,
        'college_notifications': college_notifications,
        'university_notifications': university_notifications,
    }
    return render(request, 'public/student/notifications.html', context)


@login_required
@faculty_required
def faculty_notifications(request):
    """Faculty views exam notifications"""
    faculty = request.user.faculty_profile
    college = faculty.college
    
    college_notifications = ExamNotification.objects.filter(
        college=college,
        notification_type='college',
        is_active=True
    )
    
    university_notifications = ExamNotification.objects.filter(
        notification_type='university',
        is_active=True
    )
    
    context = {
        'faculty': faculty,
        'college': college,
        'college_notifications': college_notifications,
        'university_notifications': university_notifications,
    }
    return render(request, 'public/faculty/notifications.html', context)


@login_required
@principal_required
def principal_notifications(request):
    """Principal views and manages notifications"""
    faculty = request.user.faculty_profile
    college = faculty.college
    
    college_notifications = ExamNotification.objects.filter(college=college)
    university_notifications = ExamNotification.objects.filter(
        notification_type='university',
        is_active=True
    )
    
    context = {
        'faculty': faculty,
        'college': college,
        'college_notifications': college_notifications,
        'university_notifications': university_notifications,
    }
    return render(request, 'public/principal/notifications.html', context)


@login_required
@principal_required
def principal_add_notification(request):
    """Principal adds a college exam notification"""
    faculty = request.user.faculty_profile
    college = faculty.college
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        priority = request.POST.get('priority', 'normal')
        exam_date = request.POST.get('exam_date') or None
        
        if not title or not content:
            messages.error(request, 'Title and content are required.')
        else:
            ExamNotification.objects.create(
                notification_type='college',
                title=title,
                content=content,
                priority=priority,
                college=college,
                created_by=request.user,
                exam_date=exam_date
            )
            messages.success(request, 'Notification created successfully!')
            return redirect('public:principal_notifications')
    
    context = {
        'faculty': faculty,
        'college': college,
    }
    return render(request, 'public/principal/add_notification.html', context)


# ============================================================
# STUDENT EXAM RESULTS VIEWS
# ============================================================

@login_required
@student_required
def student_results(request):
    """Student views their exam results"""
    student = request.user.studentprofile
    
    # Get all published exams for student's program
    exams = UniversityExam.objects.filter(
        program=student.program,
        result_published=True
    ).prefetch_related('subjects__results')
    
    exam_results = []
    for exam in exams:
        results = StudentResult.objects.filter(
            student=student,
            exam_subject__exam=exam
        ).select_related('exam_subject__course')
        
        if results.exists():
            total_marks = sum(r.marks_obtained or 0 for r in results)
            max_marks = sum(r.exam_subject.max_marks for r in results)
            percentage = round((total_marks / max_marks) * 100, 2) if max_marks > 0 else 0
            all_pass = all(r.is_pass for r in results)
            
            exam_results.append({
                'exam': exam,
                'results': results,
                'total_marks': total_marks,
                'max_marks': max_marks,
                'percentage': percentage,
                'status': 'Pass' if all_pass else 'Fail'
            })
    
    context = {
        'student': student,
        'college': student.college,
        'exam_results': exam_results,
    }
    return render(request, 'public/student/results.html', context)


# ============================================================
# PRINCIPAL QUESTION PAPER VIEWS
# ============================================================

@login_required
@principal_required
def principal_question_papers(request):
    """Principal views/downloads question papers"""
    faculty = request.user.faculty_profile
    college = faculty.college
    
    # Get released question papers
    now = timezone.now()
    papers = QuestionPaper.objects.filter(
        status='released',
        release_datetime__lte=now
    ).select_related('exam_subject__exam', 'exam_subject__course')
    
    context = {
        'faculty': faculty,
        'college': college,
        'papers': papers,
    }
    return render(request, 'public/principal/question_papers.html', context)


@login_required
@principal_required
def principal_download_paper(request, paper_id):
    """Principal downloads a question paper"""
    from academic.models import QuestionPaperDownload
    
    faculty = request.user.faculty_profile
    college = faculty.college
    
    paper = get_object_or_404(QuestionPaper, pk=paper_id, status='released')
    
    # Log the download
    QuestionPaperDownload.objects.create(
        question_paper=paper,
        college=college,
        downloaded_by=request.user
    )
    paper.download_count += 1
    paper.save()
    
    # Return the file
    response = HttpResponse(paper.paper_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{paper.title}.pdf"'
    return response


# ============================================================
# COLLEGE PORTAL NOTIFICATIONS
# ============================================================

@login_required
@college_required
def college_notifications(request):
    """College views notifications"""
    college = request.user.college_profile
    
    college_notifications = ExamNotification.objects.filter(college=college)
    university_notifications = ExamNotification.objects.filter(
        notification_type='university',
        is_active=True
    )
    
    context = {
        'college': college,
        'college_notifications': college_notifications,
        'university_notifications': university_notifications,
    }
    return render(request, 'public/college/notifications.html', context)


@login_required
@college_required
def college_add_notification(request):
    """College adds exam notification"""
    college = request.user.college_profile
    
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()
        priority = request.POST.get('priority', 'normal')
        exam_date = request.POST.get('exam_date') or None
        
        if not title or not content:
            messages.error(request, 'Title and content are required.')
        else:
            ExamNotification.objects.create(
                notification_type='college',
                title=title,
                content=content,
                priority=priority,
                college=college,
                created_by=request.user,
                exam_date=exam_date
            )
            messages.success(request, 'Notification created successfully!')
            return redirect('public:college_notifications')
    
    context = {
        'college': college,
    }
    return render(request, 'public/college/add_notification.html', context)


@login_required
@college_required
def college_question_papers(request):
    """College views/downloads question papers"""
    college = request.user.college_profile
    
    now = timezone.now()
    papers = QuestionPaper.objects.filter(
        status='released',
        release_datetime__lte=now
    ).select_related('exam_subject__exam', 'exam_subject__course')
    
    context = {
        'college': college,
        'papers': papers,
    }
    return render(request, 'public/college/question_papers.html', context)


@login_required
@college_required
def college_download_paper(request, paper_id):
    """College downloads a question paper"""
    from academic.models import QuestionPaperDownload
    
    college = request.user.college_profile
    
    paper = get_object_or_404(QuestionPaper, pk=paper_id, status='released')
    
    QuestionPaperDownload.objects.create(
        question_paper=paper,
        college=college,
        downloaded_by=request.user
    )
    paper.download_count += 1
    paper.save()
    
    response = HttpResponse(paper.paper_file, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{paper.title}.pdf"'
    return response


# ============================================================
# AJAX ENDPOINTS
# ============================================================

@login_required
def get_semester_subjects(request):
    """AJAX endpoint to get subjects for a program and semester"""
    program_id = request.GET.get('program_id')
    semester = request.GET.get('semester')
    
    if program_id and semester:
        # Get subjects from ProgramSemesterCourse
        psc_list = ProgramSemesterCourse.objects.filter(
            program_id=program_id,
            semester=semester
        ).select_related('course')
        
        data = [{'id': psc.course.pk, 'code': psc.course.code, 'title': psc.course.title} for psc in psc_list]
        return JsonResponse({'subjects': data})
    
    return JsonResponse({'subjects': []})
