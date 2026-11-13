from types import SimpleNamespace
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.db import IntegrityError, transaction
from django.http import HttpResponse
from django.test import Client, RequestFactory, SimpleTestCase, TestCase
from django.urls import reverse
from .decorators import role_required
from .forms import ProfileForm, RegistrationForm
from .models import User

PASSWORD = "A-test-only-secret-47!"

class AccessWithoutDatabaseTests(SimpleTestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_anonymous_is_redirected_to_login(self):
        request = self.factory.get('/accounts/dashboard/admin/')
        request.user = AnonymousUser()
        response = role_required(admin=True)(lambda r: HttpResponse('ok'))(request)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_wrong_role_is_denied_in_both_directions(self):
        for staff in (True, False):
            request = self.factory.get('/')
            request.user = SimpleNamespace(is_authenticated=True, is_staff=staff)
            with self.assertRaises(PermissionDenied):
                role_required(admin=not staff)(lambda r: HttpResponse('ok'))(request)

    def test_right_role_is_allowed_in_both_directions(self):
        for staff in (True, False):
            request = self.factory.get('/')
            request.user = SimpleNamespace(is_authenticated=True, is_staff=staff)
            response = role_required(admin=staff)(lambda r: HttpResponse('ok'))(request)
            self.assertEqual(response.status_code, 200)

    def test_forms_never_expose_privilege_fields(self):
        for form in (ProfileForm(), RegistrationForm()):
            for name in ('is_staff', 'is_superuser', 'groups', 'user_permissions', 'id'):
                self.assertNotIn(name, form.fields)

    def test_home_renders(self):
        response = self.client.get('/')
        self.assertContains(response, 'WorthIt')

    def test_empty_registration_shows_required_errors(self):
        response = self.client.post(reverse('accounts:register'), {})
        self.assertContains(response, 'This field is required.')

    def test_logout_get_is_not_allowed(self):
        self.assertEqual(self.client.get(reverse('accounts:logout')).status_code, 405)

    def test_missing_csrf_is_rejected(self):
        client = Client(enforce_csrf_checks=True)
        self.assertEqual(client.post(reverse('accounts:register'), {}).status_code, 403)

class AccountIntegrationTests(TestCase):
    def setUp(self):
        self.member = User.objects.create_user(username='member', email='member@example.com', password=PASSWORD,
                                              first_name='Mitchie', last_name='Espanto')
        self.admin = User.objects.create_superuser(username='manager', email='admin@example.com', password=PASSWORD)

    def registration(self, **overrides):
        data = dict(first_name='New', last_name='Member', username='newmember', email='new@example.com',
                    password1=PASSWORD, password2=PASSWORD)
        data.update(overrides)
        return self.client.post(reverse('accounts:register'), data)

    def test_registration_hashes_password_and_blocks_role_escalation(self):
        response = self.registration(is_staff='true', is_superuser='true')
        self.assertRedirects(response, reverse('accounts:login'))
        user = User.objects.get(username='newmember')
        self.assertTrue(user.check_password(PASSWORD))
        self.assertNotEqual(user.password, PASSWORD)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_registration_validates_email_confirmation_and_duplicate_identity(self):
        for changes, message in [
            ({'email': 'invalid'}, 'Enter a valid email address.'),
            ({'password2': 'mismatch'}, 'The two password fields'),
            ({'email': 'MEMBER@example.com'}, 'already registered'),
            ({'username': 'MEMBER'}, 'already taken'),
        ]:
            with self.subTest(changes=changes):
                self.assertContains(self.registration(**changes), message)
        self.assertEqual(User.objects.count(), 2)

    def test_database_rejects_duplicate_case_variant_email(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.bulk_create([User(username='third', email='MEMBER@EXAMPLE.COM')])

    def test_login_redirects_each_role(self):
        for user, destination in [(self.member, 'user_dashboard'), (self.admin, 'admin_dashboard')]:
            self.client.logout()
            response = self.client.post(reverse('accounts:login'), {'username': user.username.upper(), 'password': PASSWORD}, follow=True)
            self.assertEqual(response.request['PATH_INFO'], reverse('accounts:' + destination))
            self.assertEqual(response.status_code, 200)

    def test_bad_password_and_inactive_user_cannot_login(self):
        response = self.client.post(reverse('accounts:login'), {'username': 'member', 'password': 'wrong'})
        self.assertContains(response, 'Please enter a correct username and password')
        self.assertNotIn('_auth_user_id', self.client.session)
        self.member.is_active = False
        self.member.save()
        self.client.post(reverse('accounts:login'), {'username': 'member', 'password': PASSWORD})
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_external_next_is_ignored(self):
        response = self.client.post(reverse('accounts:login') + '?next=https://example.com',
                                    {'username': 'member', 'password': PASSWORD})
        self.assertEqual(response.url, reverse('accounts:dashboard'))

    def test_guests_are_redirected_from_all_protected_pages(self):
        for name in ('dashboard', 'user_dashboard', 'admin_dashboard', 'profile', 'profile_edit'):
            self.assertEqual(self.client.get(reverse('accounts:' + name)).status_code, 302)

    def test_url_role_bypass_is_denied(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse('accounts:admin_dashboard')).status_code, 403)
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('accounts:user_dashboard')).status_code, 403)

    def test_logout_clears_session_and_protected_access(self):
        self.client.force_login(self.member)
        self.client.post(reverse('accounts:logout'))
        self.assertNotIn('_auth_user_id', self.client.session)
        self.assertEqual(self.client.get(reverse('accounts:profile')).status_code, 302)

    def test_profile_update_is_owned_and_cannot_change_role(self):
        self.client.force_login(self.member)
        response = self.client.post(reverse('accounts:profile_edit'), dict(
            first_name='Updated', last_name='Espanto', email='updated@example.com', contact_number='+639171234567',
            id=self.admin.pk, is_staff='true', is_superuser='true'))
        self.assertRedirects(response, reverse('accounts:profile'))
        self.member.refresh_from_db()
        self.admin.refresh_from_db()
        self.assertEqual(self.member.first_name, 'Updated')
        self.assertFalse(self.member.is_staff)
        self.assertFalse(self.member.is_superuser)
        self.assertEqual(self.admin.email, 'admin@example.com')
        response = self.client.get(reverse('accounts:profile') + f'?user_id={self.admin.pk}')
        self.assertContains(response, 'updated@example.com')
        self.assertNotContains(response, 'admin@example.com')
        self.assertEqual(self.client.get(f'/accounts/profile/{self.admin.pk}/').status_code, 404)

    def test_profile_rejects_another_users_email(self):
        self.client.force_login(self.member)
        response = self.client.post(reverse('accounts:profile_edit'), dict(
            first_name='Mitchie', last_name='Espanto', email='ADMIN@example.com', contact_number=''))
        self.assertContains(response, 'already registered')
        self.member.refresh_from_db()
        self.assertEqual(self.member.email, 'member@example.com')
