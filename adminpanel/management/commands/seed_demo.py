from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
import random

from accounts.models import StudentProfile, FacultyProfile
from academic.models import Department, Program, Course, CourseOffering
from enrollment.models import Enrollment

User = get_user_model()


class Command(BaseCommand):
    help = "Seed demo data for UMS"

    def handle(self, *args, **options):
        self.stdout.write("Seeding demo data...")

        # Staff users
        staff_data = [
            {"email": "hod@uni.test", "first_name": "Head", "last_name": "Dept", "role": "faculty", "is_staff": True},
            {"email": "faculty@uni.test", "first_name": "Jane", "last_name": "Faculty", "role": "faculty", "is_staff": True},
        ]
        for s in staff_data:
            u, created = User.objects.get_or_create(email=s["email"], defaults={
                "first_name": s["first_name"],
                "last_name": s["last_name"],
                "role": s.get("role", "faculty"),
                "is_staff": s.get("is_staff", False),
                "is_active": True,
            })
            if created:
                u.set_password("adminpass")
                u.save()
                self.stdout.write(f"Created staff user: {u.email} / password=adminpass")
            else:
                self.stdout.write(f"Staff user already exists: {u.email}")

        hod_user = User.objects.get(email="hod@uni.test")
        faculty_user = User.objects.get(email="faculty@uni.test")

        # Departments (4)
        dept_names = ["Computer Science", "Mathematics", "Physics", "Business"]
        departments = []
        for i, name in enumerate(dept_names, start=1):
            code = f"DEPT{i:02d}"
            dept, created = Department.objects.get_or_create(code=code, defaults={"name": name})
            if created:
                self.stdout.write(f"Created Department: {name}")
            departments.append(dept)

        # Assign HOD to first department
        departments[0].head = FacultyProfile.objects.get_or_create(user=hod_user, defaults={"faculty_id":"HOD001"})[0]
        departments[0].head.user = hod_user
        departments[0].head.save()
        departments[0].save()

        # Programs (one per dept)
        programs = []
        for dept in departments:
            prog, _ = Program.objects.get_or_create(name=f"{dept.name} BSc", department=dept)
            programs.append(prog)

        # Courses (5)
        course_defs = [
            ("CS101", "Intro to Programming", 3.0, departments[0]),
            ("CS201", "Data Structures", 3.0, departments[0]),
            ("MA101", "Calculus I", 4.0, departments[1]),
            ("PH101", "Mechanics", 3.0, departments[2]),
            ("BU101", "Principles of Management", 3.0, departments[3]),
        ]
        courses = []
        for code, title, credits, dept in course_defs:
            c, created = Course.objects.get_or_create(code=code, defaults={"title": title, "credits": credits, "department": dept})
            if created:
                self.stdout.write(f"Created Course: {code}")
            courses.append(c)

        # CourseOfferings (3) - assign instructor to offerings
        offerings = []
        offering_defs = [
            (courses[0], "Fall", timezone.now().year, hod_user),
            (courses[1], "Fall", timezone.now().year, faculty_user),
            (courses[2], "Spring", timezone.now().year, faculty_user),
        ]
        for course, term, year, instr_user in offering_defs:
            instr_fp, _ = FacultyProfile.objects.get_or_create(user=instr_user, defaults={"faculty_id": f"F_{instr_user.email.split('@')[0]}"})
            off, created = CourseOffering.objects.get_or_create(course=course, term=term, year=year, defaults={"instructor": instr_fp, "capacity": 50})
            if created:
                self.stdout.write(f"Created CourseOffering: {course.code} {term} {year}")
            offerings.append(off)

        # Students (10)
        students = []
        for i in range(1, 11):
            email = f"student{i:02d}@uni.test"
            user, created = User.objects.get_or_create(email=email, defaults={
                "first_name": f"Student{i}",
                "last_name": "Demo",
                "role": "student",
                "is_active": True,
            })
            if created:
                user.set_password("studentpass")
                user.save()
                self.stdout.write(f"Created student user: {email} / password=studentpass")
            sp, _ = StudentProfile.objects.get_or_create(user=user, defaults={"student_id": f"S{i:04d}", "program": programs[i % len(programs)].name})
            students.append(sp)

        # Enrollments (15) - random student->offering pairs
        enrolled_pairs = set()
        total_needed = 15
        attempts = 0
        while len(enrolled_pairs) < total_needed and attempts < 200:
            s = random.choice(students)
            o = random.choice(offerings)
            key = (s.pk, o.pk)
            if key in enrolled_pairs:
                attempts += 1
                continue
            Enrollment.objects.get_or_create(student=s, offering=o, defaults={"status":"enrolled"})
            enrolled_pairs.add(key)
            self.stdout.write(f"Enrolled {s} -> {o}")
            attempts += 1

        self.stdout.write(self.style.SUCCESS("Seeding complete."))