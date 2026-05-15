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
        "and highly descriptive complaint summary based on the provided title, category, and "
        "any visual evidence if an image is attached. "
        "Write 2-3 short sentences explaining the issue clearly as if you are the citizen "
        "reporting it. DO NOT include markdown formatting, bullet points, or placeholders. "
        "Just return plain text that can be directly pasted into a text area."
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
