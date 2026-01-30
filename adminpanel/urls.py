from django.urls import path
from . import views

app_name = "adminpanel"

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    
    # Students
    path('students/', views.students_list, name='students'),
    path('students/add/', views.student_add, name='student_add'),
    path('students/<int:pk>/edit/', views.student_edit, name='student_edit'),
    path('students/<int:pk>/delete/', views.student_delete, name='student_delete'),
    
    # Courses
    path('courses/', views.courses_list, name='courses'),
    path('courses/add/', views.course_add, name='course_add'),
    path('courses/<int:pk>/edit/', views.course_edit, name='course_edit'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),
    
    # Departments
    path('departments/', views.departments_list, name='departments'),
    path('departments/add/', views.department_add, name='department_add'),
    path('departments/<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('departments/<int:pk>/delete/', views.department_delete, name='department_delete'),
    
    # Faculty
    path('faculty/', views.faculty_list, name='faculty_list'),
    path('faculty/add/', views.faculty_add, name='faculty_add'),
    path('faculty/<int:pk>/edit/', views.faculty_edit, name='faculty_edit'),
    path('faculty/<int:pk>/delete/', views.faculty_delete, name='faculty_delete'),
    
    # Enrollments
    path('enrollments/', views.enrollments_list, name='enrollments'),
    
    # Colleges
    path('colleges/', views.colleges_list, name='colleges'),
    path('colleges/add/', views.college_add, name='college_add'),
    path('colleges/<int:pk>/', views.college_detail, name='college_detail'),
    path('colleges/<int:pk>/edit/', views.college_edit, name='college_edit'),
    path('colleges/<int:pk>/delete/', views.college_delete, name='college_delete'),
    path('colleges/<int:pk>/approve/', views.college_approve, name='college_approve'),
    path('colleges/<int:pk>/programs/', views.college_programs_affiliation, name='college_programs_affiliation'),
    path('colleges/<int:pk>/affiliation/', views.college_affiliation, name='college_affiliation'),
    
    # University Notifications
    path('notifications/', views.university_notifications, name='notifications'),
    path('notifications/add/', views.notification_add, name='notification_add'),
    path('notifications/<int:pk>/edit/', views.notification_edit, name='notification_edit'),
    path('notifications/<int:pk>/delete/', views.notification_delete, name='notification_delete'),
    
    # University Exams
    path('exams/', views.exams_list, name='exams'),
    path('exams/add/', views.exam_add, name='exam_add'),
    path('exams/<int:pk>/', views.exam_detail, name='exam_detail'),
    path('exams/<int:pk>/edit/', views.exam_edit, name='exam_edit'),
    path('exams/<int:pk>/delete/', views.exam_delete, name='exam_delete'),
    path('exams/<int:pk>/add-subject/', views.exam_add_subject, name='exam_add_subject'),
    path('exams/<int:pk>/delete-subject/<int:subject_pk>/', views.exam_delete_subject, name='exam_delete_subject'),
    path('exams/<int:pk>/publish-results/', views.exam_publish_results, name='exam_publish_results'),
    
    # Results Entry
    path('exams/<int:exam_pk>/results/', views.results_entry, name='results_entry'),
    path('exams/<int:exam_pk>/results/<int:subject_pk>/', views.results_by_subject, name='results_by_subject'),
    
    # Question Papers
    path('question-papers/', views.question_papers, name='question_papers'),
    path('question-papers/add/', views.question_paper_add, name='question_paper_add'),
    path('question-papers/<int:pk>/edit/', views.question_paper_edit, name='question_paper_edit'),
    path('question-papers/<int:pk>/delete/', views.question_paper_delete, name='question_paper_delete'),
    path('question-papers/<int:pk>/release/', views.question_paper_release, name='question_paper_release'),
    
    # Programs
    path('programs/', views.programs_list, name='programs'),
    path('programs/add/', views.program_add, name='program_add'),
    path('programs/<int:pk>/', views.program_detail, name='program_detail'),
    path('programs/<int:pk>/edit/', views.program_edit, name='program_edit'),
    path('programs/<int:pk>/delete/', views.program_delete, name='program_delete'),
    path('programs/<int:pk>/add-course/', views.program_add_course, name='program_add_course'),
    path('programs/<int:pk>/remove-course/<int:course_pk>/', views.program_remove_course, name='program_remove_course'),
    path('programs/<int:pk>/move-course/', views.program_move_course, name='program_move_course'),
    
    # AJAX endpoints
    path('api/exam-subjects/', views.get_exam_subjects, name='get_exam_subjects'),
    path('api/program-courses/', views.get_program_courses, name='get_program_courses'),
]
