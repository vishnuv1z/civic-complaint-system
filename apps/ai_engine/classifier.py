"""
AI Complaint Classifier.

Uses NLP to classify and categorize complaints from text or image input.
Will be fully implemented in Phase 8 with scikit-learn and/or OpenAI API.
"""


import os
import json
import base64
from groq import Groq
from django.conf import settings

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


def encode_image_to_base64(image_path: str) -> str:
    """Encode an image file to a base64 string."""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image: {e}")
        return None


def classify_complaint(text: str, image_path: str = None) -> dict:
    """
    Classify a complaint based on text and/or image input using Groq API.

    Args:
        text: The complaint description text.
        image_path: Optional path to an uploaded complaint image.

    Returns:
        dict with keys: 'category', 'confidence', 'department_code'
    """
    api_key = os.environ.get("GROQ_API_KEY")
    
    if not api_key:
        print("GROQ_API_KEY not set. Returning default classification.")
        return {
            'category': 'Other',
            'confidence': 0.0,
            'department_code': None,
        }

    client = Groq(api_key=api_key)
    categories_str = ", ".join([f"'{c}'" for c in COMPLAINT_CATEGORIES])
    
    system_prompt = (
        f"You are a civic complaint classifier. Your task is to categorize the given complaint into "
        f"EXACTLY ONE of the following categories: {categories_str}. "
        f"Respond ONLY with a valid JSON object containing 'category' (string) and 'confidence' (float between 0.0 and 1.0). "
        f"Do not include markdown blocks or any other text."
    )

    try:
        messages = [
            {"role": "system", "content": system_prompt}
        ]

        # Use text model by default
        model = "llama-3.3-70b-versatile"
        
        # If an image is provided, construct a multimodal message and use the specified image model
        if image_path and os.path.exists(image_path):
            base64_image = encode_image_to_base64(image_path)
            if base64_image:
                model = "meta-llama/llama-4-scout-17b-16e-instruct" # User-specified model for image classification
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Complaint description: {text}"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                })
            else:
                messages.append({"role": "user", "content": f"Complaint description: {text}"})
        else:
            messages.append({"role": "user", "content": f"Complaint description: {text}"})

        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            response_format={"type": "json_object"}
        )

        response_content = completion.choices[0].message.content
        result = json.loads(response_content)
        
        category = result.get('category', 'Other')
        if category not in COMPLAINT_CATEGORIES:
            category = 'Other'
            
        return {
            'category': category,
            'confidence': result.get('confidence', 0.8),
            'department_code': None,
        }

    except Exception as e:
        print(f"Error calling Groq API: {e}")
        return {
            'category': 'Other',
            'confidence': 0.0,
            'department_code': None,
        }
