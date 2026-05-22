import os
import django
from dotenv import load_dotenv

def test_sms(phone_number):
    load_dotenv()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
    django.setup()
    
    from apps.notifications.services import send_sms_notification
    
    print(f"Attempting to send SMS to {phone_number}...")
    success = send_sms_notification(phone_number, "Test message from AI Complaint System!")
    if success:
        print("Successfully sent SMS!")
    else:
        print("Failed to send SMS. Check your Twilio credentials or ensure the phone number is verified on Twilio.")

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        test_sms(sys.argv[1])
    else:
        print("Please provide a phone number as an argument. Example: python test_twilio.py +1234567890")
