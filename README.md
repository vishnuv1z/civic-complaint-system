# Civiq

Civiq is a Django-based civic complaint management system. Citizens can submit civic complaints with text, location details, and an optional image. The system uses AI-assisted validation and classification to help filter irrelevant submissions, categorize complaints, assign priority, and route accepted complaints to the appropriate department queue.

## Features

- Citizen registration, login, profile management, and logout.
- Department staff registration and login.
- Complaint submission with title, description, category, address, map coordinates, and optional image upload.
- AI-assisted complaint classification, title rewriting, category selection, and description generation through Groq.
- AI genuineness validation before a complaint is saved, with local keyword fallback when Groq is unavailable.
- Unique complaint tracking IDs.
- Public complaint tracking by tracking ID.
- Citizen complaint list and complaint detail pages.
- Public complaint explore page and complaint map.
- Department-scoped staff queue and complaint review workflow.
- Complaint statuses: pending, under review, forwarded, in progress, resolved, rejected, and closed.
- Priority assignment based on category and seriousness keywords.
- Department routing based on configured complaint categories.
- Email and SMS forwarding to department authority contacts after staff review.
- Admin dashboard with complaint counts, category statistics, priority statistics, department workload, and recent complaints.
- Accepted complaints store AI category, AI confidence, genuineness score, validation reason, and validation flags.

## Tech Stack

- Python
- Django 6
- Django REST Framework, installed but no public API routes are currently enabled
- SQLite for development
- PostgreSQL settings for production
- Django templates with Tailwind-style utility classes
- JavaScript for map, image preview, and AI helper actions
- Leaflet for maps
- Groq API for AI text and image analysis
- Twilio for SMS sending
- Pillow for image upload support
- WhiteNoise and Gunicorn for production deployment support

## Project Structure

```text
ai-complaint-system/
|-- apps/
|   |-- accounts/        # Custom user model, authentication, profiles
|   |-- ai_engine/       # AI classification, validation, routing helpers, AI endpoints
|   |-- complaints/      # Complaint models, forms, views, admin, tests
|   |-- departments/     # Department and department staff models/views
|   `-- notifications/   # Email and SMS helper services
|-- config/
|   |-- urls.py
|   `-- settings/
|       |-- base.py
|       |-- development.py
|       `-- production.py
|-- requirements/
|   |-- base.txt
|   |-- dev.txt
|   `-- prod.txt
|-- services/
|   `-- complaint_service.py
|-- static/
|-- templates/
|-- manage.py
`-- test_twilio.py
```

## Main Routes

- `/` - Home page
- `/admin/` - Django admin
- `/accounts/login/` - Citizen login
- `/accounts/register/` - Citizen registration
- `/accounts/department/login/` - Department staff login
- `/accounts/department/register/` - Department staff registration
- `/accounts/profile/` - User profile
- `/complaints/submit/` - Submit complaint
- `/complaints/` - Logged-in user's complaints
- `/complaints/explore/` - Public complaint list
- `/complaints/track/` - Track complaint by tracking ID
- `/complaints/map/` - Public complaint map
- `/complaints/staff/` - Department staff queue
- `/complaints/staff/<tracking_id>/` - Department staff review page
- `/complaints/<tracking_id>/` - Complaint detail
- `/dashboard/` - Admin dashboard
- `/departments/settings/` - Department contact settings
- `/ai/generate-description/` - AI description helper
- `/ai/rewrite-title/` - AI title rewrite helper
- `/ai/categorize/` - AI category helper

## Setup

Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements/base.txt
pip install -r requirements/dev.txt
```

Create a `.env` file in the project root if you need to override settings or enable external services:

```env
DJANGO_SECRET_KEY=change-this-secret
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

GROQ_API_KEY=

TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
```

Run migrations and start the development server:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open the app at:

```text
http://127.0.0.1:8000/
```

## Configuration Notes

Development settings use SQLite and the console email backend.

Production settings use PostgreSQL environment variables:

```env
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=
```

Production email settings:

```env
EMAIL_HOST=
EMAIL_PORT=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_USE_TLS=
DEFAULT_FROM_EMAIL=
```

## Running Tests

```bash
python manage.py test
```

To run the complaint and AI-related tests only:

```bash
python manage.py test apps.ai_engine apps.complaints
```

## License

This project is licensed under the MIT License. See `LICENSE` for details.
