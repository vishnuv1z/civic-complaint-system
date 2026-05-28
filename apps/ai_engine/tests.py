from unittest.mock import patch

from django.test import TestCase

from .genuineness import analyze_complaint_genuineness, local_genuineness_check


class ComplaintGenuinenessTests(TestCase):
    def test_local_check_accepts_civic_complaints_and_rejects_spam(self):
        civic_result = local_genuineness_check(
            title='Broken street light',
            description='The street light near the bus stop is not working at night.',
            category='Street Light',
        )
        spam_result = local_genuineness_check(
            title='Buy crypto now',
            description='Visit this discount lottery promotion link and earn money quickly.',
            category='Other',
        )

        self.assertTrue(civic_result['is_genuine'])
        self.assertFalse(spam_result['is_genuine'])
        self.assertIn('spam_terms', spam_result['flags'])

    def test_analyzer_uses_local_fallback_without_api_key(self):
        with patch.dict('os.environ', {}, clear=True):
            result = analyze_complaint_genuineness(
                title='Large pothole',
                description='There is a large pothole on the road near the school.',
                category='Road & Pothole',
            )

        self.assertTrue(result['is_genuine'])
        self.assertEqual(result['source'], 'local')
