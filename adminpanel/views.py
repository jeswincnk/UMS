from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.utils import timezone
from accounts.models import StudentProfile, FacultyProfile, College, CollegeAffiliatedDepartment, CollegeAffiliatedProgram
from academic.models import Course, Department, CourseOffering, Program, ExamNotification, UniversityExam, ExamSubject, StudentResult, QuestionPaper, ProgramSemesterCourse
from enrollment.models import Enrollment
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.utils import OperationalError, ProgrammingError
from django.http import JsonResponse

User = get_user_model()


def staff_required(user):
    return user.is_active and user.is_staff


@login_required
@user_passes_test(staff_required)
def dashboard(request):
    try:
        students_count = StudentProfile.objects.count()
    except (OperationalError, ProgrammingError):
        students_count = 0

    try:
        courses_count = Course.objects.count()
    except (OperationalError, ProgrammingError):
        courses_count = 0

    try:
        enrollments_count = Enrollment.objects.count()
    except (OperationalError, ProgrammingError):
        enrollments_count = 0
    
    try:
        faculty_count = FacultyProfile.objects.count()
    except (OperationalError, ProgrammingError):
        faculty_count = 0
    
    try:
        departments_count = Department.objects.count()
    except (OperationalError, ProgrammingError):
        departments_count = 0
    
    try:
        colleges_count = College.objects.count()
        pending_colleges_count = College.objects.filter(status='pending').count()
        affiliated_colleges_count = College.objects.filter(affiliation_status='approved').count()
        pending_affiliation_count = College.objects.filter(affiliation_status='pending').count()
    except (OperationalError, ProgrammingError):
        colleges_count = 0
        pending_colleges_count = 0
        affiliated_colleges_count = 0
        pending_affiliation_count = 0
    
    try:
        programs_count = Program.objects.count()
    except (OperationalError, ProgrammingError):
        programs_count = 0

    context = {
        'students_count': students_count,
        'courses_count': courses_count,
        'enrollments_count': enrollments_count,
        'faculty_count': faculty_count,
        'departments_count': departments_count,
        'colleges_count': colleges_count,
        'pending_colleges_count': pending_colleges_count,
        'affiliated_colleges_count': affiliated_colleges_count,
        'pending_affiliation_count': pending_affiliation_count,
        'programs_count': programs_count,
    }
    return render(request, 'adminpanel/dashboard.html', context)


# ========== STUDENT VIEWS ==========

@login_required
@user_passes_test(staff_required)
def students_list(request):
    q = request.GET.get('q', '').strip()
    qs = StudentProfile.objects.select_related('user', 'college').all().order_by('-pk')
    if q:
        qs = qs.filter(
            Q(pk__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(user__email__icontains=q) |
            Q(program__icontains=q) |
            Q(college__name__icontains=q)
        )

    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    try:
        students = paginator.page(page)
    except PageNotAnInteger:
        students = paginator.page(1)
    except EmptyPage:
        students = paginator.page(paginator.num_pages)

    context = {
        'students': students,
        'query': q,
    }
    return render(request, 'adminpanel/students.html', context)


@login_required
@user_passes_test(staff_required)
def student_add(request):
    colleges = College.objects.all().order_by('name')
    programs = Program.objects.all().order_by('name')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        program_id = request.POST.get('program', '').strip()
        dob = request.POST.get('dob', '').strip() or None
        password = request.POST.get('password', '').strip()
        college_id = request.POST.get('college', '').strip()
        college = College.objects.filter(id=college_id).first() if college_id else None
        program = Program.objects.filter(id=program_id).first() if program_id else None
        # Check for duplicate email
        if User.objects.filter(email=email).exclude(pk=student.user.pk).exists():
            messages.error(request, 'A user with this email already exists.')
        else:
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='student'
            )
            student = StudentProfile.objects.create(
                user=user,
                program=program,
                dob=dob,
                college=college
            )
            messages.success(request, f'Student {first_name} {last_name} created successfully. ID: {student.student_id}')
            return redirect('adminpanel:students')
    
    return render(request, 'adminpanel/student_form.html', {'action': 'Add', 'colleges': colleges, 'programs': programs})


@login_required
@user_passes_test(staff_required)
def student_edit(request, pk):
    student = get_object_or_404(StudentProfile, pk=pk)
    colleges = College.objects.all().order_by('name')
    programs = Program.objects.all().order_by('name')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        program = request.POST.get('program', '').strip()
        dob = request.POST.get('dob', '').strip() or None
        college_id = request.POST.get('college', '').strip()
        college = College.objects.filter(id=college_id).first() if college_id else None
        # Check for duplicate email
        if User.objects.filter(email=email).exclude(pk=student.user.pk).exists():
            messages.error(request, 'A user with this email already exists.')
        else:
            student.user.email = email
            student.user.first_name = first_name
            student.user.last_name = last_name
            student.user.save()
            student.program = program
            student.dob = dob
            student.college = college
            student.save()
            messages.success(request, f'Student {first_name} {last_name} updated successfully.')
            return redirect('adminpanel:students')
    
    return render(request, 'adminpanel/student_form.html', {'action': 'Edit', 'student': student, 'colleges': colleges, 'programs': programs})


@login_required
@user_passes_test(staff_required)
def student_delete(request, pk):
    student = get_object_or_404(StudentProfile, pk=pk)
    if request.method == 'POST':
        user = student.user
        student.delete()
        user.delete()
        messages.success(request, 'Student deleted successfully.')
        return redirect('adminpanel:students')
    return render(request, 'adminpanel/student_confirm_delete.html', {'student': student})


# ========== COURSE VIEWS ==========

@login_required
@user_passes_test(staff_required)
def courses_list(request):
    q = request.GET.get('q', '').strip()
    qs = Course.objects.select_related('department').all().order_by('code')
    if q:
        qs = qs.filter(
            Q(code__icontains=q) |
            Q(title__icontains=q) |
            Q(department__name__icontains=q)
        )

    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    try:
        courses = paginator.page(page)
    except PageNotAnInteger:
        courses = paginator.page(1)
    except EmptyPage:
        courses = paginator.page(paginator.num_pages)

    context = {
        'courses': courses,
        'query': q,
    }
    return render(request, 'adminpanel/courses.html', context)


@login_required
@user_passes_test(staff_required)
def course_add(request):
    departments = Department.objects.all().order_by('name')
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        title = request.POST.get('title', '').strip()
        credits = request.POST.get('credits', '3.0').strip()
        department_id = request.POST.get('department', '').strip()
        
        if not code or not title:
            messages.error(request, 'Code and Title are required.')
        elif Course.objects.filter(code=code).exists():
            messages.error(request, 'A course with this code already exists.')
        else:
            course = Course.objects.create(
                code=code,
                title=title,
                credits=credits,
                department_id=department_id if department_id else None
            )
            messages.success(request, f'Course {code} created successfully.')
            return redirect('adminpanel:courses')
    
    return render(request, 'adminpanel/course_form.html', {'action': 'Add', 'departments': departments})


@login_required
@user_passes_test(staff_required)
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    departments = Department.objects.all().order_by('name')
    
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        title = request.POST.get('title', '').strip()
        credits = request.POST.get('credits', '3.0').strip()
        department_id = request.POST.get('department', '').strip()
        
        if not code or not title:
            messages.error(request, 'Code and Title are required.')
        elif Course.objects.filter(code=code).exclude(pk=pk).exists():
            messages.error(request, 'A course with this code already exists.')
        else:
            course.code = code
            course.title = title
            course.credits = credits
            course.department_id = department_id if department_id else None
            course.save()
            
            messages.success(request, f'Course {code} updated successfully.')
            return redirect('adminpanel:courses')
    
    return render(request, 'adminpanel/course_form.html', {'action': 'Edit', 'course': course, 'departments': departments})


@login_required
@user_passes_test(staff_required)
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted successfully.')
        return redirect('adminpanel:courses')
    return render(request, 'adminpanel/course_confirm_delete.html', {'course': course})


# ========== DEPARTMENT VIEWS ==========

@login_required
@user_passes_test(staff_required)
def departments_list(request):
    q = request.GET.get('q', '').strip()
    qs = Department.objects.all().order_by('name')
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(code__icontains=q))

    context = {
        'departments': qs,
        'query': q,
    }
    return render(request, 'adminpanel/departments.html', context)


@login_required
@user_passes_test(staff_required)
def department_add(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        
        if not name or not code:
            messages.error(request, 'Name and Code are required.')
        elif Department.objects.filter(code=code).exists():
            messages.error(request, 'A department with this code already exists.')
        else:
            Department.objects.create(name=name, code=code)
            messages.success(request, f'Department {name} created successfully.')
            return redirect('adminpanel:departments')
    
    return render(request, 'adminpanel/department_form.html', {'action': 'Add'})


@login_required
@user_passes_test(staff_required)
def department_edit(request, pk):
    department = get_object_or_404(Department, pk=pk)
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip()
        
        if not name or not code:
            messages.error(request, 'Name and Code are required.')
        elif Department.objects.filter(code=code).exclude(pk=pk).exists():
            messages.error(request, 'A department with this code already exists.')
        else:
            department.name = name
            department.code = code
            department.save()
            messages.success(request, f'Department {name} updated successfully.')
            return redirect('adminpanel:departments')
    
    return render(request, 'adminpanel/department_form.html', {'action': 'Edit', 'department': department})


@login_required
@user_passes_test(staff_required)
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Department deleted successfully.')
        return redirect('adminpanel:departments')
    return render(request, 'adminpanel/department_confirm_delete.html', {'department': department})


# ========== FACULTY VIEWS ==========

@login_required
@user_passes_test(staff_required)
def faculty_list(request):
    q = request.GET.get('q', '').strip()
    qs = FacultyProfile.objects.select_related('user', 'college').prefetch_related('departments').all().order_by('pk')
    if q:
        qs = qs.filter(
            Q(pk__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(user__email__icontains=q) |
            Q(departments__name__icontains=q)
        ).distinct()

    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    try:
        faculty = paginator.page(page)
    except PageNotAnInteger:
        faculty = paginator.page(1)
    except EmptyPage:
        faculty = paginator.page(paginator.num_pages)

    context = {
        'faculty_list': faculty,
        'query': q,
    }
    return render(request, 'adminpanel/faculty.html', context)


@login_required
@user_passes_test(staff_required)
def faculty_add(request):
    departments = Department.objects.all().order_by('name')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        department_id = request.POST.get('department', '').strip()
        qualification = request.POST.get('qualification', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not email or not password:
            messages.error(request, 'Email and Password are required.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
        else:
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
                role='faculty',
                is_staff=True
            )
            faculty = FacultyProfile.objects.create(
                user=user,
                department_id=department_id if department_id else None,
                qualification=qualification
            )
            messages.success(request, f'Faculty {first_name} {last_name} created successfully. ID: {faculty.faculty_id}')
            return redirect('adminpanel:faculty_list')
    
    return render(request, 'adminpanel/faculty_form.html', {'action': 'Add', 'departments': departments})


@login_required
@user_passes_test(staff_required)
def faculty_edit(request, pk):
    faculty = get_object_or_404(FacultyProfile, pk=pk)
    departments = Department.objects.all().order_by('name')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        department_id = request.POST.get('department', '').strip()
        qualification = request.POST.get('qualification', '').strip()
        
        if User.objects.filter(email=email).exclude(pk=faculty.user.pk).exists():
            messages.error(request, 'A user with this email already exists.')
        else:
            faculty.user.email = email
            faculty.user.first_name = first_name
            faculty.user.last_name = last_name
            faculty.user.save()
            
            faculty.department_id = department_id if department_id else None
            faculty.qualification = qualification
            faculty.save()
            
            messages.success(request, f'Faculty {first_name} {last_name} updated successfully.')
            return redirect('adminpanel:faculty_list')
    
    return render(request, 'adminpanel/faculty_form.html', {'action': 'Edit', 'faculty': faculty, 'departments': departments})


@login_required
@user_passes_test(staff_required)
def faculty_delete(request, pk):
    faculty = get_object_or_404(FacultyProfile, pk=pk)
    if request.method == 'POST':
        user = faculty.user
        faculty.delete()
        user.delete()
        messages.success(request, 'Faculty member deleted successfully.')
        return redirect('adminpanel:faculty_list')
    return render(request, 'adminpanel/faculty_confirm_delete.html', {'faculty': faculty})


# ========== ENROLLMENT VIEWS ==========

@login_required
@user_passes_test(staff_required)
def enrollments_list(request):
    q = request.GET.get('q', '').strip()
    qs = Enrollment.objects.select_related('student', 'student__user', 'offering', 'offering__course').all().order_by('-enrolled_at')
    if q:
        qs = qs.filter(
            Q(student__pk__icontains=q) |
            Q(student__user__email__icontains=q) |
            Q(offering__course__code__icontains=q) |
            Q(offering__course__title__icontains=q)
        )

    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    try:
        enrollments = paginator.page(page)
    except PageNotAnInteger:
        enrollments = paginator.page(1)
    except EmptyPage:
        enrollments = paginator.page(paginator.num_pages)

    context = {
        'enrollments': enrollments,
        'query': q,
    }
    return render(request, 'adminpanel/enrollments.html', context)


# ========== COLLEGE VIEWS ==========

@login_required
@user_passes_test(staff_required)
def colleges_list(request):
    q = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', '').strip()
    affiliation_filter = request.GET.get('affiliation', '').strip()
    
    qs = College.objects.select_related('user').all().order_by('-created_at')
    
    if q:
        qs = qs.filter(
            Q(name__icontains=q) |
            Q(code__icontains=q) |
            Q(user__email__icontains=q)
        )
    
    if status_filter:
        qs = qs.filter(status=status_filter)
    
    if affiliation_filter:
        qs = qs.filter(affiliation_status=affiliation_filter)

    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    try:
        colleges = paginator.page(page)
    except PageNotAnInteger:
        colleges = paginator.page(1)
    except EmptyPage:
        colleges = paginator.page(paginator.num_pages)

    context = {
        'colleges': colleges,
        'query': q,
        'status_filter': status_filter,
        'affiliation_filter': affiliation_filter,
    }
    return render(request, 'adminpanel/colleges.html', context)


@login_required
@user_passes_test(staff_required)
def college_add(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        established_year = request.POST.get('established_year', '').strip()
        password = request.POST.get('password', '').strip()
        
        if not email or not name or not code or not password:
            messages.error(request, 'Email, Name, Code, and Password are required.')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'A user with this email already exists.')
        elif College.objects.filter(code=code).exists():
            messages.error(request, 'A college with this code already exists.')
        else:
            user = User.objects.create_user(
                email=email,
                password=password,
                first_name=name,
                role='college'
            )
            college = College.objects.create(
                user=user,
                name=name,
                code=code,
                address=address,
                phone=phone,
                established_year=int(established_year) if established_year else None
            )
            messages.success(request, f'College {name} created successfully. ID: {college.college_id}')
            return redirect('adminpanel:colleges')
    
    return render(request, 'adminpanel/college_form.html', {'action': 'Add'})


@login_required
@user_passes_test(staff_required)
def college_edit(request, pk):
    college = get_object_or_404(College, pk=pk)
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        name = request.POST.get('name', '').strip()
        code = request.POST.get('code', '').strip().upper()
        address = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        established_year = request.POST.get('established_year', '').strip()
        
        if not email or not name or not code:
            messages.error(request, 'Email, Name, and Code are required.')
        elif User.objects.filter(email=email).exclude(pk=college.user.pk).exists():
            messages.error(request, 'A user with this email already exists.')
        elif College.objects.filter(code=code).exclude(pk=pk).exists():
            messages.error(request, 'A college with this code already exists.')
        else:
            college.user.email = email
            college.user.first_name = name
            college.user.save()
            
            college.name = name
            college.code = code
            college.address = address
            college.phone = phone
            college.established_year = int(established_year) if established_year else None
            college.save()
            
            messages.success(request, f'College {name} updated successfully.')
            return redirect('adminpanel:colleges')
    
    return render(request, 'adminpanel/college_form.html', {'action': 'Edit', 'college': college})


@login_required
@user_passes_test(staff_required)
def college_delete(request, pk):
    college = get_object_or_404(College, pk=pk)
    if request.method == 'POST':
        user = college.user
        college.delete()
        user.delete()
        messages.success(request, 'College deleted successfully.')
        return redirect('adminpanel:colleges')
    return render(request, 'adminpanel/college_confirm_delete.html', {'college': college})


@login_required
@user_passes_test(staff_required)
def college_detail(request, pk):
    college = get_object_or_404(College, pk=pk)
    affiliated_departments = college.affiliated_departments.select_related('department').all()
    students = college.students.select_related('user').all()[:10]
    faculty = FacultyProfile.objects.filter(college=college).select_related('user').prefetch_related('departments')[:10]
    
    # Affiliated programs grouped by department
    affiliated_programs_by_dept = {}
    affiliated_programs = college.affiliated_programs.select_related('program__department').all()
    for aff_prog in affiliated_programs:
        dept = aff_prog.program.department
        if dept.id not in affiliated_programs_by_dept:
            affiliated_programs_by_dept[dept.id] = {
                'department': dept,
                'programs': []
            }
        affiliated_programs_by_dept[dept.id]['programs'].append(aff_prog.program)
    
    context = {
        'college': college,
        'affiliated_departments': affiliated_departments,
        'affiliated_programs_by_dept': affiliated_programs_by_dept,
        'faculty': faculty,
        'total_faculty': FacultyProfile.objects.filter(college=college).count(),
        'students': students,
        'total_students': college.students.count(),
    }
    return render(request, 'adminpanel/college_detail.html', context)


@login_required
@user_passes_test(staff_required)
def college_approve(request, pk):
    college = get_object_or_404(College, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        if action == 'approve':
            college.status = 'approved'
            college.approved_at = timezone.now()
            college.approved_by = request.user
            college.save()
            messages.success(request, f'College {college.name} has been approved.')
        elif action == 'reject':
            college.status = 'rejected'
            college.save()
            messages.warning(request, f'College {college.name} has been rejected.')
        
        return redirect('adminpanel:college_detail', pk=pk)
    
    return redirect('adminpanel:college_detail', pk=pk)


@login_required
@user_passes_test(staff_required)
def college_affiliation(request, pk):
    college = get_object_or_404(College, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        if action == 'approve_affiliation':
            college.affiliation_status = 'approved'
            college.affiliation_approved_at = timezone.now()
            college.save()
            messages.success(request, f'Affiliation approved for {college.name}. The college can now enroll students.')
        elif action == 'reject_affiliation':
            college.affiliation_status = 'rejected'
            college.save()
            messages.warning(request, f'Affiliation rejected for {college.name}.')
        
        return redirect('adminpanel:college_detail', pk=pk)
    
    return redirect('adminpanel:college_detail', pk=pk)


@login_required
@user_passes_test(staff_required)
def college_programs_affiliation(request, pk):
    """Manage which programs a college is affiliated with (program-wise)"""
    college = get_object_or_404(College, pk=pk)
    all_departments = Department.objects.all().order_by('name')
    # Get all programs grouped by department
    departments_with_programs = []
    affiliated_program_ids = set(college.affiliated_programs.values_list('program_id', flat=True))

    for dept in all_departments:
        programs = Program.objects.filter(department=dept).order_by('name')
        departments_with_programs.append({
            'department': dept,
            'programs': programs,
        })

    if request.method == 'POST':
        selected_programs = request.POST.getlist('programs')
        # Clear existing affiliations and add new ones
        college.affiliated_programs.all().delete()
        for prog_id in selected_programs:
            CollegeAffiliatedProgram.objects.create(
                college=college,
                program_id=prog_id
            )
        # Optionally update department affiliations as well
        dept_ids = set(Program.objects.filter(id__in=selected_programs).values_list('department_id', flat=True))
        college.affiliated_departments.all().delete()
        for dept_id in dept_ids:
            CollegeAffiliatedDepartment.objects.get_or_create(
                college=college,
                department_id=dept_id
            )
        messages.success(request, f'Programs updated for {college.name}.')
        return redirect('adminpanel:college_detail', pk=pk)

    context = {
        'college': college,
        'departments': departments_with_programs,
        'affiliated_program_ids': affiliated_program_ids,
    }
    return render(request, 'adminpanel/college_programs_affiliation.html', context)


# ========== UNIVERSITY NOTIFICATIONS ==========

@login_required
@user_passes_test(staff_required)
def university_notifications(request):
    """List all university exam notifications"""
    notifications = ExamNotification.objects.filter(notification_type='university').order_by('-created_at')
    
    paginator = Paginator(notifications, 10)
    page = request.GET.get('page')
    try:
        notifications = paginator.page(page)
    except PageNotAnInteger:
        notifications = paginator.page(1)
    except EmptyPage:
        notifications = paginator.page(paginator.num_pages)
    
    context = {
        'notifications': notifications,
    }
    return render(request, 'adminpanel/notifications.html', context)


@login_required
@user_passes_test(staff_required)
def notification_add(request):
    """Add a new university notification"""
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        priority = request.POST.get('priority', 'normal')
        exam_date = request.POST.get('exam_date') or None
        
        ExamNotification.objects.create(
            notification_type='university',
            title=title,
            content=content,
            priority=priority,
            exam_date=exam_date,
            created_by=request.user,
        )
        messages.success(request, 'University notification created successfully.')
        return redirect('adminpanel:notifications')
    
    return render(request, 'adminpanel/notification_form.html', {})


@login_required
@user_passes_test(staff_required)
def notification_edit(request, pk):
    """Edit a university notification"""
    notification = get_object_or_404(ExamNotification, pk=pk, notification_type='university')
    
    if request.method == 'POST':
        notification.title = request.POST.get('title')
        notification.content = request.POST.get('content')
        notification.priority = request.POST.get('priority', 'normal')
        notification.exam_date = request.POST.get('exam_date') or None
        notification.is_active = 'is_active' in request.POST
        notification.save()
        messages.success(request, 'Notification updated successfully.')
        return redirect('adminpanel:notifications')
    
    context = {
        'notification': notification,
    }
    return render(request, 'adminpanel/notification_form.html', context)


@login_required
@user_passes_test(staff_required)
def notification_delete(request, pk):
    """Delete a university notification"""
    notification = get_object_or_404(ExamNotification, pk=pk, notification_type='university')
    
    if request.method == 'POST':
        notification.delete()
        messages.success(request, 'Notification deleted successfully.')
        return redirect('adminpanel:notifications')
    
    context = {
        'notification': notification,
    }
    return render(request, 'adminpanel/notification_confirm_delete.html', context)


# ========== UNIVERSITY EXAMS ==========

@login_required
@user_passes_test(staff_required)
def exams_list(request):
    """List all university exams"""
    exams = UniversityExam.objects.select_related('program').order_by('-exam_start_date')
    
    paginator = Paginator(exams, 10)
    page = request.GET.get('page')
    try:
        exams = paginator.page(page)
    except PageNotAnInteger:
        exams = paginator.page(1)
    except EmptyPage:
        exams = paginator.page(paginator.num_pages)
    
    context = {
        'exams': exams,
    }
    return render(request, 'adminpanel/exams.html', context)


@login_required
@user_passes_test(staff_required)
def exam_add(request):
    """Add a new university exam"""
    programs = Program.objects.all().order_by('name')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        program_id = request.POST.get('program')
        semester = request.POST.get('semester')
        academic_year = request.POST.get('academic_year')
        exam_start_date = request.POST.get('exam_start_date')
        exam_end_date = request.POST.get('exam_end_date')
        
        exam = UniversityExam.objects.create(
            name=name,
            program_id=program_id,
            semester=semester,
            academic_year=academic_year,
            exam_start_date=exam_start_date,
            exam_end_date=exam_end_date,
        )
        messages.success(request, f'Exam "{name}" created successfully.')
        return redirect('adminpanel:exam_detail', pk=exam.pk)
    
    context = {
        'programs': programs,
    }
    return render(request, 'adminpanel/exam_form.html', context)


@login_required
@user_passes_test(staff_required)
def exam_detail(request, pk):
    """View exam details and manage subjects"""
    exam = get_object_or_404(UniversityExam, pk=pk)
    subjects = exam.subjects.select_related('course').all()
    
    # Get courses for the exam's program department that are not already added
    added_course_ids = subjects.values_list('course_id', flat=True)
    available_courses = Course.objects.filter(department=exam.program.department).exclude(id__in=added_course_ids)
    
    context = {
        'exam': exam,
        'subjects': subjects,
        'available_courses': available_courses,
    }
    return render(request, 'adminpanel/exam_detail.html', context)


@login_required
@user_passes_test(staff_required)
def exam_edit(request, pk):
    """Edit a university exam"""
    exam = get_object_or_404(UniversityExam, pk=pk)
    programs = Program.objects.all().order_by('name')
    
    if request.method == 'POST':
        exam.name = request.POST.get('name')
        exam.program_id = request.POST.get('program')
        exam.semester = request.POST.get('semester')
        exam.academic_year = request.POST.get('academic_year')
        exam.exam_start_date = request.POST.get('exam_start_date')
        exam.exam_end_date = request.POST.get('exam_end_date')
        exam.save()
        messages.success(request, 'Exam updated successfully.')
        return redirect('adminpanel:exam_detail', pk=pk)
    
    context = {
        'exam': exam,
        'programs': programs,
    }
    return render(request, 'adminpanel/exam_form.html', context)


@login_required
@user_passes_test(staff_required)
def exam_delete(request, pk):
    """Delete a university exam"""
    exam = get_object_or_404(UniversityExam, pk=pk)
    
    if request.method == 'POST':
        exam.delete()
        messages.success(request, 'Exam deleted successfully.')
        return redirect('adminpanel:exams')
    
    context = {
        'exam': exam,
    }
    return render(request, 'adminpanel/exam_confirm_delete.html', context)


@login_required
@user_passes_test(staff_required)
def exam_add_subject(request, pk):
    """Add a subject to an exam"""
    exam = get_object_or_404(UniversityExam, pk=pk)
    
    if request.method == 'POST':
        course_id = request.POST.get('course')
        max_marks = request.POST.get('max_marks', 100)
        pass_marks = request.POST.get('pass_marks', 40)
        exam_date = request.POST.get('exam_date') or None
        
        ExamSubject.objects.create(
            exam=exam,
            course_id=course_id,
            max_marks=max_marks,
            pass_marks=pass_marks,
            exam_date=exam_date,
        )
        messages.success(request, 'Subject added to exam.')
    
    return redirect('adminpanel:exam_detail', pk=pk)


@login_required
@user_passes_test(staff_required)
def exam_delete_subject(request, pk, subject_pk):
    """Delete a subject from an exam"""
    exam = get_object_or_404(UniversityExam, pk=pk)
    subject = get_object_or_404(ExamSubject, pk=subject_pk, exam=exam)
    
    if request.method == 'POST':
        subject.delete()
        messages.success(request, 'Subject removed from exam.')
    
    return redirect('adminpanel:exam_detail', pk=pk)


@login_required
@user_passes_test(staff_required)
def exam_publish_results(request, pk):
    """Publish exam results"""
    exam = get_object_or_404(UniversityExam, pk=pk)
    
    if request.method == 'POST':
        exam.result_published = True
        exam.result_published_at = timezone.now()
        exam.save()
        messages.success(request, 'Results published successfully. Students can now view their results.')
    
    return redirect('adminpanel:exam_detail', pk=pk)


# ========== STUDENT RESULTS ==========

@login_required
@user_passes_test(staff_required)
def results_entry(request, exam_pk):
    """Entry point for results - select subject"""
    exam = get_object_or_404(UniversityExam, pk=exam_pk)
    subjects = exam.subjects.select_related('course').all()
    
    context = {
        'exam': exam,
        'subjects': subjects,
    }
    return render(request, 'adminpanel/results_entry.html', context)


@login_required
@user_passes_test(staff_required)
def results_by_subject(request, exam_pk, subject_pk):
    """Enter/Edit results for a specific subject"""
    exam = get_object_or_404(UniversityExam, pk=exam_pk)
    subject = get_object_or_404(ExamSubject, pk=subject_pk, exam=exam)
    
    # Get students enrolled in the exam's program and semester
    students = StudentProfile.objects.filter(
        program=exam.program,
        semester=exam.semester
    ).select_related('user', 'college')
    
    # Get existing results
    existing_results = {r.student_id: r for r in subject.results.all()}
    
    if request.method == 'POST':
        for student in students:
            marks_key = f'marks_{student.pk}'
            if marks_key in request.POST:
                marks = request.POST.get(marks_key)
                if marks and marks.strip():
                    marks_int = int(marks)
                    result, created = StudentResult.objects.get_or_create(
                        student=student,
                        exam_subject=subject,
                        defaults={'marks_obtained': marks_int, 'entered_by': request.user}
                    )
                    if not created:
                        result.marks_obtained = marks_int
                        result.entered_by = request.user
                        result.save()
        
        messages.success(request, f'Results saved for {subject.course.title}.')
        return redirect('adminpanel:results_entry', exam_pk=exam_pk)
    
    # Prepare student data with results
    student_data = []
    for student in students:
        result = existing_results.get(student.pk)
        student_data.append({
            'student': student,
            'result': result,
        })
    
    context = {
        'exam': exam,
        'subject': subject,
        'student_data': student_data,
    }
    return render(request, 'adminpanel/results_by_subject.html', context)


# ========== QUESTION PAPERS ==========

@login_required
@user_passes_test(staff_required)
def question_papers(request):
    """List all question papers"""
    papers = QuestionPaper.objects.select_related(
        'exam_subject__exam__program', 'exam_subject__course'
    ).order_by('-uploaded_at')
    
    paginator = Paginator(papers, 10)
    page = request.GET.get('page')
    try:
        papers = paginator.page(page)
    except PageNotAnInteger:
        papers = paginator.page(1)
    except EmptyPage:
        papers = paginator.page(paginator.num_pages)
    
    context = {
        'papers': papers,
    }
    return render(request, 'adminpanel/question_papers.html', context)


@login_required
@user_passes_test(staff_required)
def question_paper_add(request):
    """Upload a new question paper"""
    exams = UniversityExam.objects.filter(
        exam_start_date__gte=timezone.now().date()
    ).order_by('exam_start_date')
    
    if request.method == 'POST':
        exam_subject_id = request.POST.get('exam_subject')
        title = request.POST.get('title')
        release_datetime = request.POST.get('release_datetime')
        paper_file = request.FILES.get('paper_file')
        status = request.POST.get('status', 'draft')
        
        QuestionPaper.objects.create(
            exam_subject_id=exam_subject_id,
            title=title,
            paper_file=paper_file,
            release_datetime=release_datetime,
            status=status,
            uploaded_by=request.user,
        )
        messages.success(request, 'Question paper uploaded successfully.')
        return redirect('adminpanel:question_papers')
    
    context = {
        'exams': exams,
    }
    return render(request, 'adminpanel/question_paper_form.html', context)


@login_required
@user_passes_test(staff_required)
def question_paper_edit(request, pk):
    """Edit a question paper"""
    paper = get_object_or_404(QuestionPaper, pk=pk)
    exams = UniversityExam.objects.all().order_by('-exam_start_date')
    
    if request.method == 'POST':
        paper.title = request.POST.get('title')
        paper.release_datetime = request.POST.get('release_datetime')
        paper.status = request.POST.get('status', 'draft')
        
        if 'paper_file' in request.FILES:
            paper.paper_file = request.FILES.get('paper_file')
        
        paper.save()
        messages.success(request, 'Question paper updated successfully.')
        return redirect('adminpanel:question_papers')
    
    context = {
        'paper': paper,
        'exams': exams,
    }
    return render(request, 'adminpanel/question_paper_form.html', context)


@login_required
@user_passes_test(staff_required)
def question_paper_delete(request, pk):
    """Delete a question paper"""
    paper = get_object_or_404(QuestionPaper, pk=pk)
    
    if request.method == 'POST':
        paper.delete()
        messages.success(request, 'Question paper deleted successfully.')
        return redirect('adminpanel:question_papers')
    
    context = {
        'paper': paper,
    }
    return render(request, 'adminpanel/question_paper_confirm_delete.html', context)


@login_required
@user_passes_test(staff_required)
def question_paper_release(request, pk):
    """Manually release a question paper"""
    paper = get_object_or_404(QuestionPaper, pk=pk)
    
    if request.method == 'POST':
        paper.status = 'released'
        paper.released_at = timezone.now()
        paper.save()
        messages.success(request, 'Question paper released to colleges.')
    
    return redirect('adminpanel:question_papers')


@login_required
@user_passes_test(staff_required)
def get_exam_subjects(request):
    """AJAX endpoint to get subjects for an exam"""
    exam_id = request.GET.get('exam_id')
    if exam_id:
        subjects = ExamSubject.objects.filter(exam_id=exam_id).select_related('course')
        data = [{'id': s.pk, 'name': f"{s.course.code} - {s.course.title}"} for s in subjects]
        return JsonResponse({'subjects': data})
    return JsonResponse({'subjects': []})


# ========== PROGRAMS MANAGEMENT ==========

@login_required
@user_passes_test(staff_required)
def programs_list(request):
    """List all programs"""
    programs = Program.objects.select_related('department').all().order_by('department__name', 'name')
    
    context = {
        'programs': programs,
    }
    return render(request, 'adminpanel/programs.html', context)


@login_required
@user_passes_test(staff_required)
def program_add(request):
    """Add a new program"""
    departments = Department.objects.all().order_by('name')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        department_id = request.POST.get('department')
        duration_years = request.POST.get('duration_years', 4)
        
        program = Program.objects.create(
            name=name,
            department_id=department_id,
            duration_years=duration_years,
        )
        messages.success(request, f'Program "{name}" created successfully.')
        return redirect('adminpanel:program_detail', pk=program.pk)
    
    context = {
        'departments': departments,
    }
    return render(request, 'adminpanel/program_form.html', context)


@login_required
@user_passes_test(staff_required)
def program_detail(request, pk):
    """View program details with semester-wise courses"""
    program = get_object_or_404(Program, pk=pk)
    
    # Get total semesters (2 per year)
    total_semesters = program.duration_years * 2
    
    # Organize courses by semester
    semester_courses = {}
    for sem in range(1, total_semesters + 1):
        semester_courses[sem] = ProgramSemesterCourse.objects.filter(
            program=program, semester=sem
        ).select_related('course')
    
    # Get available courses for adding
    added_course_ids = ProgramSemesterCourse.objects.filter(program=program).values_list('course_id', flat=True)
    available_courses = Course.objects.exclude(id__in=added_course_ids).order_by('code')
    
    context = {
        'program': program,
        'total_semesters': total_semesters,
        'semester_courses': semester_courses,
        'available_courses': available_courses,
        'semester_range': range(1, total_semesters + 1),
    }
    return render(request, 'adminpanel/program_detail.html', context)


@login_required
@user_passes_test(staff_required)
def program_edit(request, pk):
    """Edit a program"""
    program = get_object_or_404(Program, pk=pk)
    departments = Department.objects.all().order_by('name')
    
    if request.method == 'POST':
        program.name = request.POST.get('name')
        program.department_id = request.POST.get('department')
        program.duration_years = request.POST.get('duration_years', 4)
        program.save()
        messages.success(request, 'Program updated successfully.')
        return redirect('adminpanel:program_detail', pk=pk)
    
    context = {
        'program': program,
        'departments': departments,
    }
    return render(request, 'adminpanel/program_form.html', context)


@login_required
@user_passes_test(staff_required)
def program_delete(request, pk):
    """Delete a program"""
    program = get_object_or_404(Program, pk=pk)
    
    if request.method == 'POST':
        program.delete()
        messages.success(request, 'Program deleted successfully.')
        return redirect('adminpanel:programs')
    
    context = {
        'program': program,
    }
    return render(request, 'adminpanel/program_confirm_delete.html', context)


@login_required
@user_passes_test(staff_required)
def program_add_course(request, pk):
    """Add a course to a program semester"""
    program = get_object_or_404(Program, pk=pk)
    
    if request.method == 'POST':
        course_id = request.POST.get('course')
        semester = request.POST.get('semester')
        is_elective = 'is_elective' in request.POST
        
        # Check if course already exists in this program
        if ProgramSemesterCourse.objects.filter(program=program, course_id=course_id).exists():
            messages.warning(request, 'This course is already added to this program.')
        else:
            ProgramSemesterCourse.objects.create(
                program=program,
                course_id=course_id,
                semester=semester,
                is_elective=is_elective,
            )
            messages.success(request, 'Course added to semester successfully.')
    
    return redirect('adminpanel:program_detail', pk=pk)


@login_required
@user_passes_test(staff_required)
def program_remove_course(request, pk, course_pk):
    """Remove a course from a program"""
    program = get_object_or_404(Program, pk=pk)
    
    if request.method == 'POST':
        ProgramSemesterCourse.objects.filter(
            program=program, course_id=course_pk
        ).delete()
        messages.success(request, 'Course removed from program.')
    
    return redirect('adminpanel:program_detail', pk=pk)


@login_required
@user_passes_test(staff_required)
def program_move_course(request, pk):
    """Move a course to a different semester"""
    program = get_object_or_404(Program, pk=pk)
    
    if request.method == 'POST':
        psc_id = request.POST.get('psc_id')
        new_semester = request.POST.get('new_semester')
        
        psc = get_object_or_404(ProgramSemesterCourse, pk=psc_id, program=program)
        psc.semester = new_semester
        psc.save()
        messages.success(request, f'Course moved to Semester {new_semester}.')
    
    return redirect('adminpanel:program_detail', pk=pk)


@login_required
@user_passes_test(staff_required)
def get_program_courses(request):
    """AJAX endpoint to get courses for a program and semester"""
    program_id = request.GET.get('program_id')
    semester = request.GET.get('semester')
    
    if program_id and semester:
        courses = ProgramSemesterCourse.objects.filter(
            program_id=program_id, semester=semester
        ).select_related('course')
        data = [{'id': c.course.pk, 'code': c.course.code, 'title': c.course.title} for c in courses]
        return JsonResponse({'courses': data})
    return JsonResponse({'courses': []})
