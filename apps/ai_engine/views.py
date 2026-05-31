import json
import base64
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
import os
from groq import Groq

def encode_in_memory_image(uploaded_file):
    """Encode a Django InMemoryUploadedFile to a base64 string."""
    try:
        return base64.b64encode(uploaded_file.read()).decode('utf-8')
    except Exception as e:
        print(f"Error encoding image: {e}")
        return None

@login_required
@require_POST
def generate_description_view(request):
    """
    AJAX endpoint to generate a complaint description.
    Expects 'title', 'category' in POST data, and optionally 'image' in FILES.
    """
    title = request.POST.get('title', '')
    category = request.POST.get('category', '')
    image_file = request.FILES.get('image')

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return JsonResponse({'error': 'GROQ_API_KEY not configured on server.'}, status=500)

    client = Groq(api_key=api_key)
    
    system_prompt = (
        "You are an expert civic assistant. Your task is to write a clear, professional, "
        "and a short, human-style complaint summary based on the provided title, category, and "
        "any visual evidence if an image is attached. "
        "Write 1-2 short sentences explaining the issue clearly as if you are the citizen "
        "reporting it. DO NOT include markdown formatting, bullet points, or placeholders. "
        "Just return plain text that can be directly used in a text area."
    )

    messages = [{"role": "system", "content": system_prompt}]
    model = "llama-3.3-70b-versatile"

    try:
        if image_file:
            base64_image = encode_in_memory_image(image_file)
            if base64_image:
                model = "meta-llama/llama-4-scout-17b-16e-instruct" # Multi-modal model for image analysis
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Title: {title}\nCategory: {category}\nPlease write the detailed description."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                })
            else:
                messages.append({"role": "user", "content": f"Title: {title}\nCategory: {category}\nPlease write the detailed description."})
        else:
            messages.append({"role": "user", "content": f"Title: {title}\nCategory: {category}\nPlease write the detailed description."})

        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )

        generated_text = completion.choices[0].message.content.strip()
        return JsonResponse({'description': generated_text})

    except Exception as e:
        print(f"Error calling Groq API for generation: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def rewrite_title_view(request):
    """
    AJAX endpoint to rewrite a messy complaint title into a professional one.
    Expects 'title' in POST data.
    """
    raw_title = request.POST.get('title', '')
    if not raw_title:
        return JsonResponse({'error': 'Title is required.'}, status=400)

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return JsonResponse({'error': 'GROQ_API_KEY not configured.'}, status=500)

    client = Groq(api_key=api_key)
    
    system_prompt = (
        "You are an expert civic assistant. Rewrite the following messy or informal complaint "
        "title into a single, concise, professional, and clear title (maximum 8 words). "
        "Respond ONLY with the new title, no quotes, no explanations."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": raw_title}
    ]
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.3,
            max_tokens=30,
        )
        rewritten_title = completion.choices[0].message.content.strip()
        # Remove quotes if the AI added them anyway
        if rewritten_title.startswith('"') and rewritten_title.endswith('"'):
            rewritten_title = rewritten_title[1:-1]
            
        return JsonResponse({'title': rewritten_title})
    except Exception as e:
        print(f"Error rewriting title: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def categorize_complaint_view(request):
    """
    AJAX endpoint to automatically categorize a complaint based on title and optional image.
    Expects 'title' in POST data, and optionally 'image' in FILES.
    """
    title = request.POST.get('title', '')
    image_file = request.FILES.get('image')

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return JsonResponse({'error': 'GROQ_API_KEY not configured.'}, status=500)

    client = Groq(api_key=api_key)
    
    from apps.complaints.forms import CATEGORY_CHOICES
    valid_categories = [choice[0] for choice in CATEGORY_CHOICES if choice[0]]
    categories_str = ", ".join(valid_categories)
    
    system_prompt = (
        f"You are an expert civic AI classifier. Categorize the issue into exactly ONE of the following categories: {categories_str}. "
        "Respond ONLY with the exact category name from the list, nothing else."
    )

    messages = [{"role": "system", "content": system_prompt}]
    model = "llama-3.3-70b-versatile"

    try:
        if image_file:
            base64_image = encode_in_memory_image(image_file)
            if base64_image:
                model = "meta-llama/llama-4-scout-17b-16e-instruct"
                messages.append({
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Title: {title}\nWhat is the exact category from the allowed list?"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                })
            else:
                messages.append({"role": "user", "content": f"Title: {title}\nWhat is the exact category?"})
        else:
            messages.append({"role": "user", "content": f"Title: {title}\nWhat is the exact category?"})

        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_tokens=30,
        )

        predicted_category = completion.choices[0].message.content.strip()
        
        # Cleanup response just in case
        for cat in valid_categories:
            if cat.lower() in predicted_category.lower():
                predicted_category = cat
                break
                
        # Fallback to 'Other' if not perfectly matched
        if predicted_category not in valid_categories:
            predicted_category = 'Other'
            
        return JsonResponse({'category': predicted_category})

    except Exception as e:
        print(f"Error categorizing complaint: {e}")
        return JsonResponse({'error': str(e)}, status=500)
