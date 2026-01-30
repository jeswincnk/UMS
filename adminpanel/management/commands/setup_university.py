from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from accounts.models import StudentProfile, FacultyProfile, College, CollegeAffiliatedDepartment
from academic.models import Department, Program, Course, CourseOffering, ClassSlot
from enrollment.models import Enrollment, Exam, Result

User = get_user_model()


class Command(BaseCommand):
    help = "Clear existing data and setup university departments and programs"

    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("UNIVERSITY MANAGEMENT SYSTEM SETUP")
        self.stdout.write("=" * 60)
        
        # Step 1: Clear existing data
        self.stdout.write("\n[1/3] Clearing existing data...")
        self.clear_existing_data()
        
        # Step 2: Create departments
        self.stdout.write("\n[2/3] Creating departments...")
        departments = self.create_departments()
        
        # Step 3: Create programs/courses for each department
        self.stdout.write("\n[3/3] Creating programs...")
        self.create_programs(departments)
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("✓ University setup completed successfully!"))
        self.stdout.write("=" * 60)
        self.stdout.write("\nSummary:")
        self.stdout.write(f"  - Departments: {Department.objects.count()}")
        self.stdout.write(f"  - Programs: {Program.objects.count()}")
        self.stdout.write(f"  - Students: {StudentProfile.objects.count()}")
        self.stdout.write(f"  - Colleges: {College.objects.count()}")

    def clear_existing_data(self):
        """Clear all existing academic data"""
        # Delete in order of dependencies
        models_to_clear = [
            (Result, "Results"),
            (Exam, "Exams"),
            (Enrollment, "Enrollments"),
            (ClassSlot, "Class Slots"),
            (CourseOffering, "Course Offerings"),
            (Course, "Courses"),
            (Program, "Programs"),
            (CollegeAffiliatedDepartment, "College Affiliations"),
            (Department, "Departments"),
        ]
        
        for model, name in models_to_clear:
            count = model.objects.count()
            if count > 0:
                model.objects.all().delete()
                self.stdout.write(f"  ✓ Deleted {count} {name}")
        
        # Delete student profiles and their users
        student_profiles = StudentProfile.objects.all()
        student_count = student_profiles.count()
        if student_count > 0:
            user_ids = list(student_profiles.values_list('user_id', flat=True))
            student_profiles.delete()
            User.objects.filter(id__in=user_ids, role='student').delete()
            self.stdout.write(f"  ✓ Deleted {student_count} Students")
        
        # Delete faculty profiles and their users (optional - keeping for university)
        faculty_profiles = FacultyProfile.objects.all()
        faculty_count = faculty_profiles.count()
        if faculty_count > 0:
            user_ids = list(faculty_profiles.values_list('user_id', flat=True))
            faculty_profiles.delete()
            User.objects.filter(id__in=user_ids, role='faculty').delete()
            self.stdout.write(f"  ✓ Deleted {faculty_count} Faculty")
        
        # Delete college profiles and their users
        college_profiles = College.objects.all()
        college_count = college_profiles.count()
        if college_count > 0:
            user_ids = list(college_profiles.values_list('user_id', flat=True))
            college_profiles.delete()
            User.objects.filter(id__in=user_ids, role='college').delete()
            self.stdout.write(f"  ✓ Deleted {college_count} Colleges")

    def create_departments(self):
        """Create the 7 university departments"""
        departments_data = [
            {"name": "Department of Commerce", "code": "COM"},
            {"name": "Department of Computer Science", "code": "CS"},
            {"name": "Department of Business Administration", "code": "BBA"},
            {"name": "Department of English", "code": "ENG"},
            {"name": "Department of Economics", "code": "ECO"},
            {"name": "Department of Mathematics", "code": "MATH"},
            {"name": "Department of Law", "code": "LAW"},
        ]
        
        departments = {}
        for dept_data in departments_data:
            dept = Department.objects.create(**dept_data)
            departments[dept_data["code"]] = dept
            self.stdout.write(f"  ✓ Created: {dept.name}")
        
        return departments

    def create_programs(self, departments):
        """Create programs for each department"""
        programs_data = {
            "COM": [
                {"name": "BCom (Finance)", "duration_years": 3},
                {"name": "BCom (Co-operation)", "duration_years": 3},
                {"name": "MCom", "duration_years": 2},
                {"name": "PhD in Commerce", "duration_years": 3},
            ],
            "CS": [
                {"name": "BSc Computer Science", "duration_years": 3},
                {"name": "BCA", "duration_years": 3},
                {"name": "MSc Computer Science", "duration_years": 2},
                {"name": "PhD in Computer Science", "duration_years": 3},
            ],
            "BBA": [
                {"name": "BBA", "duration_years": 3},
                {"name": "MBA", "duration_years": 2},
                {"name": "PhD in Management", "duration_years": 3},
            ],
            "ENG": [
                {"name": "BA English", "duration_years": 3},
                {"name": "MA English", "duration_years": 2},
                {"name": "PhD in English", "duration_years": 3},
            ],
            "ECO": [
                {"name": "BA Economics", "duration_years": 3},
                {"name": "MA Economics", "duration_years": 2},
                {"name": "PhD in Economics", "duration_years": 3},
            ],
            "MATH": [
                {"name": "BSc Mathematics", "duration_years": 3},
                {"name": "MSc Mathematics", "duration_years": 2},
                {"name": "PhD in Mathematics", "duration_years": 3},
            ],
            "LAW": [
                {"name": "LLB", "duration_years": 3},
                {"name": "LLM", "duration_years": 2},
                {"name": "PhD in Law", "duration_years": 3},
            ],
        }
        
        for dept_code, programs in programs_data.items():
            dept = departments[dept_code]
            for prog_data in programs:
                Program.objects.create(
                    name=prog_data["name"],
                    department=dept,
                    duration_years=prog_data["duration_years"]
                )
            self.stdout.write(f"  ✓ Created {len(programs)} programs for {dept.name}")
