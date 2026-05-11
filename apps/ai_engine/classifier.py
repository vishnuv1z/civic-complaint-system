"""
AI Complaint Classifier.

Uses NLP to classify and categorize complaints from text or image input.
Will be fully implemented in Phase 8 with scikit-learn and/or OpenAI API.
"""


# Complaint categories the AI will classify into
COMPLAINT_CATEGORIES = [
    'Road & Pothole',
    'Water Supply',
    'Drainage & Sewage',
    'Electricity',
    'Garbage & Sanitation',
    'Street Light',
    'Public Transport',
    'Noise Pollution',
    'Illegal Construction',
    'Park & Playground',
    'Traffic Signal',
    'Public Safety',
    'Other',
]


def classify_complaint(text: str, image_path: str = None) -> dict:
    """
    Classify a complaint based on text and/or image input.

    Args:
        text: The complaint description text.
        image_path: Optional path to an uploaded complaint image.

    Returns:
        dict with keys: 'category', 'confidence', 'department_code'

    TODO: Implement in Phase 8 using:
        - Text: scikit-learn TF-IDF + classifier or OpenAI API
        - Image: OpenAI Vision API or custom CNN
    """
    # Placeholder — returns default values until AI is integrated
    return {
        'category': 'Other',
        'confidence': 0.0,
        'department_code': None,
    }
