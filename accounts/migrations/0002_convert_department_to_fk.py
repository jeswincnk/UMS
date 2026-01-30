from django.db import migrations, models
import django.db.models.deletion

def forwards(apps, schema_editor):
    FacultyProfile = apps.get_model('accounts', 'FacultyProfile')
    Department = apps.get_model('academic', 'Department')

    # For each FacultyProfile, try to find a matching Department by name or code (case-insensitive).
    for fp in FacultyProfile.objects.all():
        old_val = getattr(fp, 'department', None)
        if not old_val:
            continue
        # old_val may be string (from CharField). If it's already an int/ForeignKey id, skip.
        # Attempt to match by name then code.
        dept = Department.objects.filter(name__iexact=str(old_val)).first()
        if not dept:
            dept = Department.objects.filter(code__iexact=str(old_val)).first()
        if dept:
            # department_new is the FK we add below; set by id to avoid model-level field issues
            fp.department_new_id = dept.id
            fp.save()

def reverse(apps, schema_editor):
    FacultyProfile = apps.get_model('accounts', 'FacultyProfile')
    # On reverse, copy FK back to string column `department_old` if desired.
    for fp in FacultyProfile.objects.all():
        if getattr(fp, 'department', None):
            try:
                fp.department_old = fp.department.name
                fp.save()
            except Exception:
                pass

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('academic', '0001_initial'),
    ]

    operations = [
        # Add a temporary FK field
        migrations.AddField(
            model_name='facultyprofile',
            name='department_new',
            field=models.ForeignKey(null=True, blank=True, on_delete=django.db.models.deletion.SET_NULL, to='academic.department'),
        ),
        # Data migration to populate department_new from the old charfield
        migrations.RunPython(forwards, reverse),
        # Remove the old charfield
        migrations.RemoveField(
            model_name='facultyprofile',
            name='department',
        ),
        # Rename department_new -> department
        migrations.RenameField(
            model_name='facultyprofile',
            old_name='department_new',
            new_name='department',
        ),
    ]