from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Task


class AccessControlTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='testpass123',
            email='admin@example.com',
        )
        self.user = User.objects.create_user(username='usuario', password='testpass123')
        self.other_user = User.objects.create_user(username='otro', password='testpass123')

    def test_login_page_does_not_show_register_link(self):
        response = self.client.get(reverse('login'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Regístrate')

    def test_register_url_is_removed(self):
        response = self.client.get('/register/')

        self.assertEqual(response.status_code, 404)

    def test_app_views_require_active_session(self):
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])

    def test_profile_page_is_available_for_authenticated_users(self):
        self.client.login(username='usuario', password='testpass123')
        response = self.client.get(reverse('profile'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Perfil de usuario')
        self.assertContains(response, 'Cerrar sesión')

    def test_superuser_can_create_and_assign_to_any_user(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.post(reverse('task_create'), {
            'title': 'Tarea del admin',
            'description': 'Asignada por admin',
            'color': '#ffffff',
            'asignado_a': self.user.pk,
        })

        self.assertEqual(response.status_code, 302)
        task = Task.objects.get(title='Tarea del admin')
        self.assertEqual(task.asignado_a, self.user)

    def test_normal_user_can_only_complete_own_tasks(self):
        own_task = Task.objects.create(
            title='Tarea propia',
            asignado_a=self.user,
            status=Task.Status.PENDING,
        )
        other_task = Task.objects.create(
            title='Tarea ajena',
            asignado_a=self.other_user,
            status=Task.Status.PENDING,
        )

        self.client.login(username='usuario', password='testpass123')
        response = self.client.post(reverse('task_complete', args=[own_task.pk]))

        self.assertEqual(response.status_code, 302)
        own_task.refresh_from_db()
        self.assertEqual(own_task.status, Task.Status.COMPLETED)

        not_found = self.client.post(reverse('task_complete', args=[other_task.pk]))
        self.assertEqual(not_found.status_code, 404)

    def test_normal_user_cannot_access_task_management(self):
        task = Task.objects.create(
            title='Tarea propia',
            asignado_a=self.user,
            status=Task.Status.PENDING,
        )
        self.client.login(username='usuario', password='testpass123')

        self.assertEqual(self.client.get(reverse('task_create')).status_code, 302)
        self.assertEqual(self.client.get(reverse('task_update', args=[task.pk])).status_code, 302)
        self.assertEqual(self.client.get(reverse('task_delete', args=[task.pk])).status_code, 302)

    def test_normal_user_gets_forbidden_on_django_admin(self):
        self.client.login(username='usuario', password='testpass123')
        response = self.client.get(reverse('admin:index'))

        self.assertEqual(response.status_code, 403)
        self.assertContains(
            response,
            'No posees los permisos necesarios para acceder.',
            status_code=403,
        )

    def test_normal_user_does_not_see_admin_button(self):
        self.client.login(username='usuario', password='testpass123')
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Admin Django')

    def test_superuser_sees_admin_button(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Admin Django')
        self.assertContains(response, reverse('admin:index'))


class SuperuserViewTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username='admin',
            password='testpass123',
            email='admin@example.com',
        )
        self.user = User.objects.create_user(username='usuario', password='testpass123')
        self.other_task = Task.objects.create(
            title='Tarea ajena',
            asignado_a=self.user,
            status=Task.Status.PENDING,
        )
        Task.objects.create(
            title='Tarea visible',
            asignado_a=self.superuser,
            status=Task.Status.PENDING,
        )

    def test_superuser_sees_all_tasks(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tarea ajena')
        self.assertContains(response, 'Tarea visible')
        self.assertContains(response, 'Asignada a:')

    def test_superuser_can_filter_tasks_by_user(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('dashboard'), {'asignado_a': str(self.user.pk)})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tarea ajena')
        self.assertNotContains(response, 'Tarea visible')
