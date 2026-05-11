# 🏛️ AI-Powered Civic Complaint Management System

A production-grade civic complaint platform where citizens submit complaints via **text or image**. The system's AI engine **classifies and categorizes** the complaint automatically, then **routes it to the respected authorities / government department**. Citizens can track their complaint status in real time.

## Tech Stack

- **Backend:** Django 6.0 + Django REST Framework
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **Frontend:** HTML, CSS (Tailwind), JavaScript
- **AI:** Python NLP libraries / OpenAI API
- **Notifications:** Email (SMTP) + SMS (Twilio)

## Quick Start

```bash
# 1. Create & activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# 2. Install dependencies
pip install -r requirements/dev.txt

# 3. Copy environment variables
cp .env.example .env         # Edit with your values

# 4. Run migrations
python manage.py makemigrations
python manage.py migrate

# 5. Create superuser
python manage.py createsuperuser

# 6. Start development server
python manage.py runserver
```

## Project Structure

```
ai-complaint-system/
├── config/          # Django project settings (split by environment)
├── apps/            # All Django apps
│   ├── accounts/    # Custom user model & authentication
│   ├── complaints/  # Core complaint CRUD
│   ├── departments/ # Government department management
│   ├── notifications/ # Email/SMS notification system
│   └── ai_engine/   # AI classification & routing
├── services/        # Cross-app business logic
├── templates/       # Global HTML templates
├── static/          # CSS, JS, images
├── media/           # User-uploaded files
└── requirements/    # Pip dependencies (base/dev/prod)
```

## License

MIT
