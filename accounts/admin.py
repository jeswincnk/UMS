from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, StudentProfile, FacultyProfile, College, CollegeAffiliatedDepartment


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal', {'fields': ('first_name', 'last_name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'user', 'college', 'program')
    list_filter = ('college',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name')


@admin.register(FacultyProfile)
class FacultyProfileAdmin(admin.ModelAdmin):
    list_display = ('faculty_id', 'user', 'college', 'designation', 'get_departments')
    list_filter = ('college', 'designation')
    filter_horizontal = ('departments',)
    
    def get_departments(self, obj):
        return ", ".join([d.name for d in obj.departments.all()])
    get_departments.short_description = 'Departments'


class CollegeAffiliatedDepartmentInline(admin.TabularInline):
    model = CollegeAffiliatedDepartment
    extra = 1


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ('college_id', 'name', 'code', 'status', 'affiliation_status', 'created_at')
    list_filter = ('status', 'affiliation_status')
    search_fields = ('name', 'code', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'approved_at', 'affiliation_applied_at', 'affiliation_approved_at')
    inlines = [CollegeAffiliatedDepartmentInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'name', 'code', 'address', 'phone', 'established_year')
        }),
        ('Approval Status', {
            'fields': ('status', 'approved_at', 'approved_by')
        }),
        ('Affiliation Status', {
            'fields': ('affiliation_status', 'affiliation_applied_at', 'affiliation_approved_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CollegeAffiliatedDepartment)
class CollegeAffiliatedDepartmentAdmin(admin.ModelAdmin):
    list_display = ('college', 'department', 'applied_at')
    list_filter = ('college', 'department')

