from django.contrib.auth.hashers import make_password
from django.db import migrations


DEMO_USERNAME = 'demo_pizarra'
DEMO_PASSWORD = 'Pizarra2026!'


def create_demo_user(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    user, _ = User.objects.get_or_create(
        username=DEMO_USERNAME,
        defaults={
            'first_name': 'Cuenta',
            'last_name': 'Demo',
            'email': '',
            'is_active': True,
        },
    )
    user.password = make_password(DEMO_PASSWORD)
    user.is_active = True
    user.save()


def delete_demo_user(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    User.objects.filter(username=DEMO_USERNAME).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('tareas', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.RunPython(create_demo_user, delete_demo_user),
    ]
