from django.contrib import admin
from .models import Department, Program, Course, CourseOffering, ClassSlot


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'head')
    search_fields = ('name', 'code')
    list_filter = ('head',)


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'duration_years')
    search_fields = ('name',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'credits', 'department')
    search_fields = ('code', 'title')
    list_filter = ('department',)


@admin.register(CourseOffering)
class CourseOfferingAdmin(admin.ModelAdmin):
    list_display = ('course', 'term', 'year', 'instructor', 'capacity')
    list_filter = ('term', 'year', 'instructor')


@admin.register(ClassSlot)
class ClassSlotAdmin(admin.ModelAdmin):
    list_display = ('offering', 'day', 'start_time', 'end_time', 'room')
    list_filter = ('day',)
