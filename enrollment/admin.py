from django.contrib import admin
from .models import Enrollment, Exam, Result


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'offering', 'status', 'enrolled_at')
    list_filter = ('status', 'enrolled_at')
    search_fields = ('student__student_id', 'student__user__email')


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('offering', 'exam_date', 'max_marks')
    list_filter = ('exam_date',)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('enrollment', 'marks_obtained', 'grade')
    search_fields = ('enrollment__student__student_id',)
