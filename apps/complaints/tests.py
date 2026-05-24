from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch

from django.core import mail
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from .forms import ComplaintForm
from .models import Complaint, ComplaintForwardLog
from apps.departments.models import Department, DepartmentStaff
from services.complaint_service import (
    assign_priority,
    create_complaint,
    forward_complaint_to_authority,
    update_complaint_status,
)


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

    def test_assign_priority_uses_category_and_seriousness(self):
        self.assertEqual(
            assign_priority('Noise Pollution', 'Loud music', 'late night noise'),
            Complaint.Priority.LOW,
        )
        self.assertEqual(
            assign_priority('Electricity', 'Power issue', 'street transformer problem'),
            Complaint.Priority.HIGH,
        )
        self.assertEqual(
            assign_priority('Park & Playground', 'Live wire in park', 'danger near children'),
            Complaint.Priority.CRITICAL,
        )

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_forward_complaint_to_authority_sends_email_and_marks_forwarded(self):
        department = Department.objects.create(
            name='Water Department',
            code='WTR',
            categories=['Water Supply'],
            contact_email='authority@example.com',
            contact_phone='9999999999',
        )
        complaint = create_complaint(
            complainant=self.user,
            title='Contaminated water',
            description='Contaminated water is coming through the pipe.',
            category='Water Supply',
            run_ai=False,
        )
        complaint.department = department
        complaint.save(update_fields=['department'])

        forward_log = forward_complaint_to_authority(
            complaint=complaint,
            forwarded_by=self.user,
            remarks='Verified and ready to send.',
        )
        complaint.refresh_from_db()

        self.assertEqual(complaint.status, Complaint.Status.FORWARDED)
        self.assertEqual(forward_log.status, ComplaintForwardLog.Status.SENT)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(complaint.tracking_id, mail.outbox[0].body)


class ComplaintSubmitViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email='submit-citizen@example.com',
            password='test-pass',
            first_name='Submit',
            last_name='Citizen',
        )

    @patch('apps.complaints.views.create_complaint')
    @patch('apps.complaints.views.analyze_complaint_genuineness')
    def test_submit_view_delegates_creation_to_service(self, mock_analyze, mock_create_complaint):
        mock_analyze.return_value = {
            'is_genuine': True,
            'confidence': 0.91,
            'reason': 'The complaint appears genuine.',
            'flags': [],
        }
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
        self.assertEqual(
            mock_create_complaint.call_args.kwargs['genuineness_result'],
            mock_analyze.return_value,
        )

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
        self.assertContains(response, 'This complaint appears unrelated to civic issues.')
        mock_create_complaint.assert_not_called()


class DepartmentStaffTriageViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.citizen = User.objects.create_user(
            email='triage-citizen@example.com',
            password='test-pass',
            first_name='Triage',
            last_name='Citizen',
        )
        self.staff_user = User.objects.create_user(
            email='department-staff@example.com',
            password='test-pass',
            first_name='Dept',
            last_name='Staff',
            role='department_staff',
        )
        self.other_staff_user = User.objects.create_user(
            email='other-staff@example.com',
            password='test-pass',
            first_name='Other',
            last_name='Staff',
            role='department_staff',
        )
        self.department = Department.objects.create(
            name='Public Works',
            code='PWD',
            categories=['Road & Pothole'],
            contact_email='pwd-authority@example.com',
        )
        self.other_department = Department.objects.create(
            name='Electricity Department',
            code='ELEC',
            categories=['Electricity'],
            contact_email='electric-authority@example.com',
        )
        DepartmentStaff.objects.create(
            user=self.staff_user,
            department=self.department,
        )
        DepartmentStaff.objects.create(
            user=self.other_staff_user,
            department=self.other_department,
        )
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

    def test_citizen_cannot_access_department_queue(self):
        self.client.force_login(self.citizen)

        response = self.client.get(reverse('complaints:staff_queue'))

        self.assertEqual(response.status_code, 302)

    def test_department_staff_sees_only_assigned_department_complaints(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(reverse('complaints:staff_queue'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.complaint.title)
        self.assertNotContains(response, self.other_complaint.title)

    def test_department_staff_can_mark_complaint_under_review(self):
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse('complaints:staff_review', kwargs={'tracking_id': self.complaint.tracking_id}),
            data={
                'action': 'under_review',
                'remarks': 'Checking details.',
            },
        )
        self.complaint.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.complaint.status, Complaint.Status.UNDER_REVIEW)
        self.assertEqual(self.complaint.status_updates.count(), 1)

    def test_department_staff_cannot_review_other_department_complaint(self):
        self.client.force_login(self.staff_user)

        response = self.client.get(
            reverse('complaints:staff_review', kwargs={'tracking_id': self.other_complaint.tracking_id})
        )

        self.assertEqual(response.status_code, 404)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_department_staff_can_forward_complaint(self):
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse('complaints:staff_review', kwargs={'tracking_id': self.complaint.tracking_id}),
            data={
                'action': 'forward',
                'remarks': 'Verified by department staff.',
            },
        )
        self.complaint.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.complaint.status, Complaint.Status.FORWARDED)
        self.assertEqual(self.complaint.forward_logs.count(), 1)
        self.assertEqual(len(mail.outbox), 1)
