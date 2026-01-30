from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def login_redirect_view(request):
    """Redirect users to appropriate dashboard based on their role"""
    user = request.user
    
    # College users
    if user.role == 'college' and hasattr(user, 'college_profile'):
        return redirect('public:college_dashboard')
    
    # Admin users
    elif user.is_staff or user.role == 'admin':
        return redirect('adminpanel:dashboard')
    
    # Student users
    elif user.role == 'student' and hasattr(user, 'studentprofile'):
        return redirect('public:student_dashboard')
    
    # Faculty users (check designation for HOD/Principal)
    elif user.role == 'faculty' and hasattr(user, 'faculty_profile'):
        faculty = user.faculty_profile
        if faculty.designation == 'principal':
            return redirect('public:principal_dashboard')
        elif faculty.designation == 'hod':
            return redirect('public:hod_dashboard')
        else:
            return redirect('public:faculty_dashboard')
    
    # Default fallback
    else:
        return redirect('public:index')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('dashboard/', include('adminpanel.urls')),
    path('login-redirect/', login_redirect_view, name='login_redirect'),
    path('', include('public.urls')),
]

# Serve media files in development
from django.conf import settings as django_settings
from django.conf.urls.static import static
if django_settings.DEBUG:
    urlpatterns += static(django_settings.MEDIA_URL, document_root=django_settings.MEDIA_ROOT)