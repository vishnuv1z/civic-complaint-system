"""
Tests for the AI engine app.
"""

from unittest.mock import patch

from django.test import TestCase

from .genuineness import analyze_complaint_genuineness, local_genuineness_check


class ComplaintGenuinenessTests(TestCase):
    def test_local_check_accepts_civic_complaint(self):
        result = local_genuineness_check(
            title='Broken street light',
            description='The street light near the bus stop is not working at night.',
            category='Street Light',
        )

        self.assertTrue(result['is_genuine'])
        self.assertIn('street', result['matched_keywords'])

    def test_local_check_rejects_spam(self):
        result = local_genuineness_check(
            title='Buy crypto now',
            description='Visit this discount lottery promotion link and earn money quickly.',
            category='Other',
        )

        self.assertFalse(result['is_genuine'])
        self.assertIn('spam_terms', result['flags'])

    def test_local_check_does_not_trust_category_alone(self):
        result = local_genuineness_check(
            title='Random note',
            description='This text does not describe any public issue clearly.',
            category='Road & Pothole',
        )

        self.assertFalse(result['is_genuine'])
        self.assertIn('no_civic_keywords', result['flags'])

    def test_analyzer_uses_local_fallback_without_api_key(self):
        with patch.dict('os.environ', {}, clear=True):
            result = analyze_complaint_genuineness(
                title='Large pothole',
                description='There is a large pothole on the road near the school.',
                category='Road & Pothole',
            )

        self.assertTrue(result['is_genuine'])
        self.assertEqual(result['source'], 'local')
