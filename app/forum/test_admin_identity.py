from django.contrib.auth import get_user_model
from django.test import Client, TestCase


class AdminIdentityTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            'operator', password='operator-moss-river-652!', is_staff=True)
        self.other = get_user_model().objects.create_user('member')

    def client_with_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.get('/login/')
        return client

    def post(self, client, path, data=None):
        return client.post(path, data or {}, HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value)

    def operator_login(self, client):
        return self.post(client, '/admin/login/', {
            'username': 'operator', 'password': 'operator-moss-river-652!', 'next': '/admin/'})

    def test_guest_cannot_change_identity_through_admin_login(self):
        client = self.client_with_csrf()
        self.post(client, '/guest/')
        guest_id = client.session['guest_id']
        self.operator_login(client)
        self.assertNotIn('_auth_user_id', client.session)
        self.assertEqual(client.session['guest_id'], guest_id)
        self.assertEqual(self.post(client, '/new/', {'title': 'No', 'body': 'No'}).status_code, 403)

    def test_member_cannot_change_identity_through_admin_login(self):
        client = self.client_with_csrf()
        client.force_login(self.other)
        self.operator_login(client)
        self.assertEqual(int(client.session['_auth_user_id']), self.other.pk)

    def test_existing_staff_cannot_switch_to_another_operator(self):
        staff = get_user_model().objects.create_user('first_operator', is_staff=True)
        client = self.client_with_csrf()
        client.force_login(staff)
        self.operator_login(client)
        self.assertEqual(int(client.session['_auth_user_id']), staff.pk)

    def test_operator_can_sign_in_after_explicitly_leaving_guest_session(self):
        client = self.client_with_csrf()
        self.post(client, '/guest/')
        self.post(client, '/leave/')
        self.operator_login(client)
        self.assertEqual(int(client.session['_auth_user_id']), self.staff.pk)
        self.assertNotIn('guest_id', client.session)
        self.assertEqual(client.get('/admin/').status_code, 200)
