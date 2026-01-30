# University Management System (UMS)

A comprehensive University Management System built with Django, featuring multi-role authentication, college management, student enrollment, faculty management, attendance tracking, and examination management.

## Features

- 🏫 **Multi-College Support** - Manage multiple affiliated colleges under a university
- 👥 **Role-Based Access** - Admin, Principal, HOD, Faculty, and Student portals
- 📚 **Academic Management** - Departments, Programs, Courses, and Semesters
- 📝 **Enrollment System** - Student enrollment and course registration
- 📊 **Attendance Tracking** - Mark and manage student attendance
- 📋 **Examination Module** - Exams, question papers, and results management
- 🔔 **Notifications** - System-wide announcements and notifications

## Tech Stack

- **Backend:** Django 4.x
- **Database:** SQLite (development) / MySQL (production)
- **Frontend:** Bootstrap 5, HTML5, CSS3
- **Authentication:** Django built-in with custom user model

---

## 🚀 Quick Start Guide

### Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- Git

### Installation

#### 1. Clone the Repository

```bash
git clone https://github.com/jeswincnk/UMS.git
cd UMS
```

#### 2. Create Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### 4. Configure Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Edit `.env` file:
```
SECRET_KEY=your-secret-key-here
DEBUG=True
```

#### 5. Run Database Migrations

```bash
python manage.py migrate
```

#### 6. Create Superuser (Admin Account)

```bash
python manage.py createsuperuser
```

#### 7. (Optional) Load Demo Data

```bash
python manage.py seed_demo
```

#### 8. Run the Development Server

```bash
python manage.py runserver
```

### Access the Application

| Portal | URL |
|--------|-----|
| Public Site | http://127.0.0.1:8000/ |
| Admin Panel | http://127.0.0.1:8000/admin/ |
| University Admin | http://127.0.0.1:8000/adminpanel/ |

---

## 📁 Project Structure

```
UMS/
├── academic/          # Academic models (Programs, Courses, Exams)
├── accounts/          # User authentication and profiles
├── adminpanel/        # University admin dashboard
├── attendance/        # Attendance tracking module
├── enrollment/        # Student enrollment management
├── finance/           # Fee and payment management
├── public/            # Public-facing views and role dashboards
├── templates/         # HTML templates
├── ums_project/       # Django project settings
├── manage.py
├── requirements.txt
└── README.md
```

## 👥 User Roles

1. **University Admin** - Full system access, manage colleges and programs
2. **College Admin** - Manage college-specific data
3. **Principal** - College oversight, faculty and student management
4. **HOD** - Department management, attendance oversight
5. **Faculty** - Course management, attendance marking
6. **Student** - View attendance, results, and notifications

---

## Notes

- The default `AUTH_USER_MODEL` is `accounts.User`
- For production, configure MySQL in environment variables; see `ums_project/settings.py`
- Make sure to set `DEBUG=False` and configure `ALLOWED_HOSTS` in production

## License

This project is for educational purposes.

---

**Developed with ❤️ using Django**
