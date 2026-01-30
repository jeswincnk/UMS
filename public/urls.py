from django.urls import path
from . import views

app_name = "public"

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('courses/', views.courses, name='courses'),
    path('contact/', views.contact, name='contact'),
    path('register/', views.college_register, name='college_register'),
    
    # College Portal
    path('college/', views.college_dashboard, name='college_dashboard'),
    path('college/profile/', views.college_profile, name='college_profile'),
    path('college/departments/', views.college_select_departments, name='college_select_departments'),
    path('college/students/', views.college_students, name='college_students'),
    path('college/students/add/', views.college_add_student, name='college_add_student'),
    path('college/students/<int:student_id>/', views.college_view_student, name='college_view_student'),
    path('college/students/<int:student_id>/edit/', views.college_edit_student, name='college_edit_student'),
    path('college/faculty/', views.college_faculty, name='college_faculty'),
    path('college/faculty/add/', views.college_add_faculty, name='college_add_faculty'),
    path('college/faculty/<int:faculty_id>/', views.college_view_faculty, name='college_view_faculty'),
    path('college/faculty/<int:faculty_id>/edit/', views.college_edit_faculty, name='college_edit_faculty'),
    path('college/notifications/', views.college_notifications, name='college_notifications'),
    path('college/notifications/add/', views.college_add_notification, name='college_add_notification'),
    path('college/question-papers/', views.college_question_papers, name='college_question_papers'),
    path('college/question-papers/<int:paper_id>/download/', views.college_download_paper, name='college_download_paper'),
    
    # Student Portal
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/', views.student_profile, name='student_profile'),
    path('student/attendance/', views.student_attendance, name='student_attendance'),
    path('student/attendance/medical-certificate/', views.student_submit_medical_certificate, name='student_submit_medical_certificate'),
    path('student/notifications/', views.student_notifications, name='student_notifications'),
    path('student/results/', views.student_results, name='student_results'),
    
    # Faculty Portal
    path('faculty/', views.faculty_dashboard, name='faculty_dashboard'),
    path('faculty/profile/', views.faculty_profile, name='faculty_profile'),
    path('faculty/attendance/', views.faculty_attendance, name='faculty_attendance'),
    path('faculty/attendance/<int:session_id>/edit/', views.faculty_edit_attendance, name='faculty_edit_attendance'),
    path('faculty/notifications/', views.faculty_notifications, name='faculty_notifications'),
    
    # HOD Portal
    path('hod/', views.hod_dashboard, name='hod_dashboard'),
    path('hod/profile/', views.hod_profile, name='hod_profile'),
    path('hod/faculty/', views.hod_faculty, name='hod_faculty'),
    path('hod/students/', views.hod_students, name='hod_students'),
    path('hod/attendance/', views.hod_attendance, name='hod_attendance'),
    path('hod/attendance/add/', views.hod_add_attendance, name='hod_add_attendance'),
    path('hod/attendance/<int:session_id>/mark/', views.hod_mark_attendance, name='hod_mark_attendance'),
    path('hod/attendance/<int:session_id>/edit/', views.hod_edit_attendance, name='hod_edit_attendance'),
    path('hod/medical-certificates/', views.hod_medical_certificates, name='hod_medical_certificates'),
    path('hod/medical-certificates/<int:cert_id>/review/', views.hod_review_certificate, name='hod_review_certificate'),
    path('hod/notifications/', views.hod_notifications, name='hod_notifications'),
    path('hod/notifications/add/', views.hod_add_notification, name='hod_add_notification'),
    
    # Principal Portal
    path('principal/', views.principal_dashboard, name='principal_dashboard'),
    path('principal/profile/', views.principal_profile, name='principal_profile'),
    path('principal/faculty/', views.principal_faculty, name='principal_faculty'),
    path('principal/students/', views.principal_students, name='principal_students'),
    path('principal/departments/', views.principal_departments, name='principal_departments'),
    path('principal/notifications/', views.principal_notifications, name='principal_notifications'),
    path('principal/notifications/add/', views.principal_add_notification, name='principal_add_notification'),
    path('principal/question-papers/', views.principal_question_papers, name='principal_question_papers'),
    path('principal/question-papers/<int:paper_id>/download/', views.principal_download_paper, name='principal_download_paper'),
    
    # AJAX endpoints
    path('api/semester-subjects/', views.get_semester_subjects, name='get_semester_subjects'),
]
