from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import ComplaintForm
from .models import Complaint
from apps.departments.models import Department
from services.complaint_service import create_complaint, update_complaint_status


class ComplaintLocationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='citizen@example.com',
            password='test-pass',
            first_name='Test',
            last_name='Citizen',
        )

    def test_complaint_form_accepts_valid_coordinates(self):
        form = ComplaintForm(data={
            'title': 'Broken street light',
            'description': 'The street light is not working.',
            'category': 'Street Light',
            'address': 'MG Road',
            'latitude': '10.850516',
            'longitude': '76.271080',
        })

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data['latitude'], Decimal('10.850516'))
        self.assertEqual(form.cleaned_data['longitude'], Decimal('76.271080'))

    def test_complaint_form_rejects_incomplete_coordinates(self):
        form = ComplaintForm(data={
            'title': 'Broken street light',
            'description': 'The street light is not working.',
            'category': 'Street Light',
            'address': 'MG Road',
            'latitude': '10.850516',
            'longitude': '',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_coordinates_api_returns_safe_marker_payload(self):
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

        response = self.client.get(reverse('complaints:coordinates_api'))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 2)
        self.assertEqual(data['mapped_count'], 1)

        mapped_payload = next(
            item for item in data['complaints']
            if item['tracking_id'] == mapped.tracking_id
        )
        self.assertEqual(mapped_payload['latitude'], 10.850516)
        self.assertEqual(mapped_payload['longitude'], 76.27108)
        self.assertTrue(mapped_payload['has_valid_coordinates'])


class ComplaintServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='service-citizen@example.com',
            password='test-pass',
            first_name='Service',
            last_name='Citizen',
        )

    @patch('services.complaint_service.classify_complaint')
    def test_create_complaint_saves_ai_metadata_and_routes_department(self, mock_classify):
        mock_classify.return_value = {
            'category': 'Road & Pothole',
            'confidence': 0.93,
        }
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
            latitude=Decimal('10.850516'),
            longitude=Decimal('76.271080'),
        )

        self.assertEqual(complaint.category, 'Road & Pothole')
        self.assertEqual(complaint.ai_category, 'Road & Pothole')
        self.assertEqual(complaint.ai_confidence, 0.93)
        self.assertEqual(complaint.department, department)
        mock_classify.assert_called_once()

    @patch('services.complaint_service.classify_complaint')
    def test_manual_category_overrides_ai_category(self, mock_classify):
        mock_classify.return_value = {
            'category': 'Road & Pothole',
            'confidence': 0.88,
        }
        department = Department.objects.create(
            name='Electrical Department',
            code='ELEC',
            categories=['Electricity'],
        )

        complaint = create_complaint(
            complainant=self.user,
            title='Power line issue',
            description='A power line is hanging low.',
            category='Electricity',
            run_ai=True,
        )

        self.assertEqual(complaint.category, 'Electricity')
        self.assertEqual(complaint.ai_category, 'Road & Pothole')
        self.assertEqual(complaint.department, department)

    def test_update_complaint_status_creates_timeline_entry(self):
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
        self.assertIsNotNone(complaint.resolved_at)
        self.assertEqual(status_update.old_status, Complaint.Status.PENDING)
        self.assertEqual(status_update.new_status, Complaint.Status.RESOLVED)


class ComplaintSubmitViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='submit-citizen@example.com',
            password='test-pass',
            first_name='Submit',
            last_name='Citizen',
        )

    @patch('apps.complaints.views.create_complaint')
    def test_submit_view_delegates_creation_to_service(self, mock_create_complaint):
        mock_create_complaint.return_value = SimpleNamespace(tracking_id='CMP-TEST-1234')
        self.client.force_login(self.user)

        response = self.client.post(reverse('complaints:submit'), data={
            'title': 'Broken street light',
            'description': 'The street light is not working.',
            'category': 'Street Light',
            'address': 'MG Road',
            'latitude': '10.850516',
            'longitude': '76.271080',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse(
            'complaints:detail',
            kwargs={'tracking_id': 'CMP-TEST-1234'},
        ))
        mock_create_complaint.assert_called_once()
