import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Create a superuser from environment variables"

    def handle(self, *args, **options):
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        
        if not email or not password:
            self.stdout.write(
                self.style.WARNING('DJANGO_SUPERUSER_EMAIL and DJANGO_SUPERUSER_PASSWORD not set. Skipping superuser creation.')
            )
            return
        
        if User.objects.filter(email=email).exists():
            # Update existing user to ensure it's a superuser
            user = User.objects.get(email=email)
            user.set_password(password)
            user.is_staff = True
            user.is_superuser = True
            user.is_active = True
            user.role = 'admin'
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Updated existing user to superuser: {email}')
            )
            return
        
        user = User.objects.create_superuser(
            email=email,
            password=password,
            first_name='Admin',
            last_name='User',
            role='admin'
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created superuser: {email}')
        )
