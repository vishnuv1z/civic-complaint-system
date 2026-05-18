from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import ComplaintForm
from .models import Complaint


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
