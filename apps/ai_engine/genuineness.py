"""
Complaint genuineness checks for pre-submission validation.
"""

import base64
import json
import os
import re

from groq import Groq


CIVIC_KEYWORDS = {
    'accident',
    'blocked',
    'broken',
    'burst',
    'collapse',
    'contaminated',
    'danger',
    'damaged',
    'drain',
    'drainage',
    'electricity',
    'flood',
    'garbage',
    'hazard',
    'illegal construction',
    'leak',
    'leakage',
    'light',
    'noise',
    'overflow',
    'park',
    'pipe',
    'pollution',
    'pothole',
    'public safety',
    'road',
    'sanitation',
    'sewage',
    'street',
    'street light',
    'supply',
    'traffic',
    'transport',
    'water',
    'wire',
}

SPAM_KEYWORDS = {
    'airdrop',
    'betting',
    'buy now',
    'casino',
    'crypto',
    'discount',
    'earn money',
    'free followers',
    'lottery',
    'promotion',
    'subscribe',
    'winner',
}

GENUINENESS_THRESHOLD = 0.65


def _normalize(text):
    return re.sub(r'\s+', ' ', (text or '').strip().lower())


def _encode_uploaded_file(uploaded_file):
    if not uploaded_file:
        return None

    try:
        position = uploaded_file.tell()
    except (AttributeError, OSError):
        position = None

    try:
        if hasattr(uploaded_file, 'seek'):
            uploaded_file.seek(0)
        encoded = base64.b64encode(uploaded_file.read()).decode('utf-8')
    except Exception:
        return None
    finally:
        if position is not None and hasattr(uploaded_file, 'seek'):
            uploaded_file.seek(position)

    return encoded


def local_genuineness_check(title, description, category):
    """Fast deterministic fallback when AI validation is unavailable."""
    title = _normalize(title)
    description = _normalize(description)
    category = _normalize(category)
    complaint_text = f"{title} {description}"
    combined = f"{complaint_text} {category}"

    flags = []
    civic_matches = sorted(keyword for keyword in CIVIC_KEYWORDS if keyword in complaint_text)

    if len(title) < 6:
        flags.append('title_too_short')
    if len(description) < 20:
        flags.append('description_too_short')
    if re.search(r'https?://|www\.', combined):
        flags.append('contains_link')
    if any(keyword in combined for keyword in SPAM_KEYWORDS):
        flags.append('spam_terms')
    if not civic_matches:
        flags.append('no_civic_keywords')

    is_genuine = not {'contains_link', 'spam_terms', 'no_civic_keywords'} & set(flags)
    is_genuine = is_genuine and len(title) >= 6 and len(description) >= 20

    if is_genuine:
        reason = 'The complaint appears related to a civic or public service issue.'
        confidence = 0.7 if civic_matches else 0.55
    else:
        reason = (
            'This complaint could not be submitted because it does not appear to '
            'describe a genuine civic or public service issue.'
        )
        confidence = 0.75

    return {
        'is_genuine': is_genuine,
        'confidence': confidence,
        'reason': reason,
        'flags': flags,
        'image_relevant': None,
        'matched_keywords': civic_matches,
        'source': 'local',
    }


def analyze_complaint_genuineness(title, description, category, image_file=None):
    """
    Validate whether a complaint is genuine and relevant before it is saved.
    Falls back to deterministic keyword checks if the AI service is unavailable.
    """
    local_result = local_genuineness_check(title, description, category)
    api_key = os.environ.get('GROQ_API_KEY')

    if not api_key:
        return local_result

    image_data = _encode_uploaded_file(image_file)
    client = Groq(api_key=api_key)
    model = 'llama-3.3-70b-versatile'

    system_prompt = (
        'You validate civic complaint submissions for a public complaint portal. '
        'Decide whether the submission describes a genuine civic/public service issue, '
        'not spam, ads, jokes, random text, abuse, or unrelated personal content. '
        'If an image is provided, check whether it is relevant to the complaint title, '
        'description, and category. Respond only as JSON with keys: is_genuine '
        '(boolean), confidence (number 0 to 1), reason (short user-facing string), '
        'flags (array of short strings), image_relevant (boolean or null).'
    )
    user_text = (
        f"Title: {title}\n"
        f"Category: {category}\n"
        f"Description: {description}\n\n"
        f"Local keyword signal: {json.dumps(local_result)}"
    )

    messages = [{'role': 'system', 'content': system_prompt}]
    if image_data:
        model = 'meta-llama/llama-4-scout-17b-16e-instruct'
        messages.append({
            'role': 'user',
            'content': [
                {'type': 'text', 'text': user_text},
                {
                    'type': 'image_url',
                    'image_url': {'url': f'data:image/jpeg;base64,{image_data}'},
                },
            ],
        })
    else:
        messages.append({'role': 'user', 'content': user_text})

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            response_format={'type': 'json_object'},
        )
        result = json.loads(completion.choices[0].message.content)
    except Exception as exc:
        local_result['flags'] = [*local_result.get('flags', []), 'ai_unavailable']
        local_result['reason'] = local_result['reason'] if local_result['is_genuine'] else (
            f"{local_result['reason']} Please provide a clearer title, description, and relevant photo."
        )
        local_result['ai_error'] = str(exc)
        return local_result

    flags = result.get('flags') or []
    if not isinstance(flags, list):
        flags = ['invalid_ai_flags']

    confidence = result.get('confidence', 0)
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0

    image_relevant = result.get('image_relevant')
    is_genuine = bool(result.get('is_genuine')) and confidence >= GENUINENESS_THRESHOLD
    if image_data and image_relevant is False and confidence >= GENUINENESS_THRESHOLD:
        is_genuine = False
        if 'image_unrelated' not in flags:
            flags.append('image_unrelated')

    reason = result.get('reason') or local_result['reason']
    if not is_genuine and 'civic' not in reason.lower() and 'image' not in reason.lower():
        reason = (
            'This complaint could not be submitted because it appears unrelated '
            'to a civic or public service issue.'
        )

    return {
        'is_genuine': is_genuine,
        'confidence': max(0.0, min(confidence, 1.0)),
        'reason': reason,
        'flags': flags,
        'image_relevant': image_relevant,
        'matched_keywords': local_result.get('matched_keywords', []),
        'source': 'ai',
    }
