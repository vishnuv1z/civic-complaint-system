from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.departments.models import Department, DepartmentStaff
from services.complaint_service import create_complaint, update_complaint_status

from .forms import ComplaintForm
from .models import Complaint


class ComplaintCoreTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='citizen@example.com',
            password='test-pass',
            first_name='Test',
            last_name='Citizen',
        )

    def test_form_requires_complete_coordinates(self):
        valid = {
            'title': 'Broken street light',
            'description': 'The street light is not working.',
            'category': 'Street Light',
            'address': 'MG Road',
            'latitude': '10.850516',
            'longitude': '76.271080',
        }

        self.assertTrue(ComplaintForm(data=valid).is_valid())
        self.assertFalse(ComplaintForm(data={**valid, 'longitude': ''}).is_valid())

    def test_coordinates_api_only_maps_complaints_with_location(self):
        mapped = Complaint.objects.create(
            complainant=self.user,
            title='Road damage',
            description='Large pothole near the junction.',
            category='Road & Pothole',
            latitude=Decimal('10.850516'),
            longitude=Decimal('76.271080'),
        )
        Complaint.objects.create(
            complainant=self.user,
            title='No location complaint',
            description='This complaint has no coordinates.',
            category='Other',
        )

        data = self.client.get(reverse('complaints:coordinates_api')).json()

        self.assertEqual(data['mapped_count'], 1)
        payload = next(item for item in data['complaints'] if item['tracking_id'] == mapped.tracking_id)
        self.assertEqual(payload['latitude'], 10.850516)
        self.assertTrue(payload['has_valid_coordinates'])

    @patch('services.complaint_service.classify_complaint')
    def test_create_complaint_routes_department_and_stores_ai_metadata(self, mock_classify):
        mock_classify.return_value = {'category': 'Road & Pothole', 'confidence': 0.93}
        department = Department.objects.create(
            name='Public Works',
            code='PWD',
            categories=['Road & Pothole'],
        )

        complaint = create_complaint(
            complainant=self.user,
            title='Large pothole',
            description='There is a large pothole near the bus stop.',
            address='Bus stop road',
        )

        self.assertEqual(complaint.category, 'Road & Pothole')
        self.assertEqual(complaint.ai_confidence, 0.93)
        self.assertEqual(complaint.department, department)

    def test_status_update_changes_complaint_and_adds_timeline_entry(self):
        complaint = create_complaint(
            complainant=self.user,
            title='Water leak',
            description='Water is leaking from the main pipe.',
            category='Water Supply',
            run_ai=False,
        )

        status_update = update_complaint_status(
            complaint=complaint,
            new_status=Complaint.Status.RESOLVED,
            changed_by=self.user,
            remarks='Fixed by field team.',
        )
        complaint.refresh_from_db()

        self.assertEqual(complaint.status, Complaint.Status.RESOLVED)
        self.assertEqual(status_update.old_status, Complaint.Status.PENDING)
        self.assertIsNotNone(complaint.resolved_at)

    @patch('apps.complaints.views.create_complaint')
    @patch('apps.complaints.views.analyze_complaint_genuineness')
    def test_submit_view_blocks_irrelevant_complaint(self, mock_analyze, mock_create_complaint):
        mock_analyze.return_value = {
            'is_genuine': False,
            'confidence': 0.89,
            'reason': 'This complaint appears unrelated to civic issues.',
            'flags': ['no_civic_keywords'],
        }
        self.client.force_login(self.user)

        response = self.client.post(reverse('complaints:submit'), data={
            'title': 'Random promotion',
            'description': 'This is a promotional message that should not be posted.',
            'category': 'Other',
            'address': 'MG Road',
            'latitude': '10.850516',
            'longitude': '76.271080',
        })

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, mock_analyze.return_value['reason'])
        mock_create_complaint.assert_not_called()


class DepartmentStaffTriageTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.citizen = User.objects.create_user('citizen@example.com', 'test-pass')
        self.staff_user = User.objects.create_user(
            'staff@example.com',
            'test-pass',
            role='department_staff',
        )
        self.department = Department.objects.create(
            name='Public Works',
            code='PWD',
            categories=['Road & Pothole'],
            contact_email='pwd-authority@example.com',
        )
        other_department = Department.objects.create(
            name='Electricity Department',
            code='ELEC',
            categories=['Electricity'],
            contact_email='electric-authority@example.com',
        )
        DepartmentStaff.objects.create(user=self.staff_user, department=self.department)
        self.complaint = create_complaint(
            complainant=self.citizen,
            title='Road pothole',
            description='Large pothole near the school road.',
            category='Road & Pothole',
            run_ai=False,
        )
        self.other_complaint = create_complaint(
            complainant=self.citizen,
            title='Live wire',
            description='Live wire is hanging near the street.',
            category='Electricity',
            run_ai=False,
        )
        self.other_complaint.department = other_department
        self.other_complaint.save(update_fields=['department'])

    def test_staff_queue_is_limited_to_assigned_department(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse('complaints:staff_queue'))

        self.assertContains(response, self.complaint.title)
        self.assertNotContains(response, self.other_complaint.title)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_staff_can_forward_own_department_complaint(self):
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse('complaints:staff_review', kwargs={'tracking_id': self.complaint.tracking_id}),
            data={'action': 'forward', 'remarks': 'Verified by department staff.'},
        )
        self.complaint.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.complaint.status, Complaint.Status.FORWARDED)
        self.assertEqual(len(mail.outbox), 1)
