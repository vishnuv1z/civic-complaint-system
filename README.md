# 🏛️ Civiq - AI-Powered Civic Complaint Management System

A **production-grade civic complaint platform** that empowers citizens to submit complaints via **text or image** to government authorities. The system leverages **AI-powered classification** to automatically categorize complaints and intelligently **route them to the appropriate government departments**. Citizens can **track complaint status in real-time** while departments manage and resolve issues through an intuitive staff interface.

---

## ✨ Core Features

### 🎯 **Complaint Management**
- **Multi-input Submission:** Citizens can submit complaints via text description and/or images
- **Auto-generated Tracking ID:** Each complaint gets a unique, shareable tracking ID (e.g., `CMP-20260511-A1B2`)
- **Rich Metadata:** Complaints include title, detailed description, geolocation (latitude/longitude), and address
- **Status Lifecycle:** Complaints progress through statuses: Pending → Under Review → Forwarded → In Progress → Resolved/Rejected → Closed
- **Priority Levels:** Auto-assigned based on keywords and category (Low, Medium, High, Critical)
- **Complaint History:** Full audit trail with timestamps for all status changes

### 🤖 **AI-Powered Classification & Routing**
- **Groq API Integration:** Advanced NLP classification with image analysis support
- **13 Category Classification:** Road & Pothole, Water Supply, Drainage & Sewage, Electricity, Garbage & Sanitation, Street Light, Public Transport, Noise Pollution, Illegal Construction, Park & Playground, Traffic Signal, Public Safety, Other
- **Confidence Scoring:** AI assigns confidence scores (0.0 – 1.0) to predictions
- **Smart Priority Assignment:** Keywords like "emergency," "accident," "danger" trigger higher priorities automatically
- **Automatic Department Routing:** System intelligently routes complaints to appropriate departments based on category

### 👥 **Role-Based Access Control**
- **Citizens:** Submit, view, and track their own complaints; view public complaint list
- **Department Staff:** Review assigned complaints, update status, provide updates, manage workload
- **Administrators:** Full system access, user management, department configuration, analytics

### 🗺️ **Geolocation & Maps**
- **GPS Coordinates:** Capture latitude/longitude for every complaint
- **Address Storage:** Full address field for reference
- **Map Visualization:** Interactive map view showing complaint locations with filtering and clustering

### 📱 **Real-Time Notifications**
- **Email Notifications:** Automated emails on complaint submission, status updates, resolution
- **SMS Alerts:** Twilio-powered SMS notifications for critical complaints and status changes
- **Customizable Templates:** Department-specific notification messages

### 📊 **Analytics & Dashboards**
- **Admin Dashboard:** 
  - Monthly resolved complaints with YoY trends
  - Currently open complaints count
  - Active department metrics
  - Recent activity feed
  - Department performance analytics
- **Staff Dashboard:** Complaint queue, priority sorting, bulk actions
- **Public Dashboard:** Anonymous complaint statistics and trends

### 🏢 **Department Management**
- **Department Profiles:** Name, code, contact info, complaint categories handled
- **Staff Assignment:** Assign staff to departments with roles (Head, Officer, Field Worker)
- **Category Mapping:** Configure which categories each department handles
- **Active/Inactive Status:** Enable/disable departments dynamically

### 👤 **User Management**
- **Custom User Model:** Email-based authentication (not username)
- **Profile Management:** User profiles with phone, address, profile picture
- **Email Verification:** Built-in email verification system
- **Account Types:** Citizen, Department Staff, Administrator roles

### 📋 **Complaint Tracking & History**
- **Public Tracking Page:** Citizens track their complaint by tracking ID without login
- **Status Timeline:** Visual timeline of all status updates with timestamps
- **Complaint Detail View:** Complete complaint information, images, and communication history
- **Bulk Export:** Export complaint lists for reporting

### 🔐 **Security & Compliance**
- **CSRF Protection:** Django's built-in CSRF middleware
- **SQL Injection Prevention:** ORM-based database queries
- **Environment-based Configuration:** Separate settings for development, production
- **Secrets Management:** Environment variables for sensitive data (API keys, database credentials)

---

## 🛠️ Tech Stack

| Category | Technology |
|----------|------------|
| **Backend Framework** | Django 6.0 |
| **REST API** | Django REST Framework (DRF) |
| **Database** | SQLite (development) / PostgreSQL (production) |
| **Frontend** | HTML5, CSS3 (Tailwind CSS), JavaScript (Vanilla) |
| **AI/NLP** | Groq API, scikit-learn |
| **Email** | SMTP (Django Mail) |
| **SMS** | Twilio API |
| **Image Processing** | Pillow, Base64 encoding |
| **Async Tasks** | Celery (ready for integration) |
| **API Documentation** | Django REST Framework browsable API |

---

## 📁 Project Structure

```
ai-complaint-system/
│
├── config/                          # Django project settings
│   ├── __init__.py
│   ├── asgi.py                     # ASGI config for production
│   ├── wsgi.py                     # WSGI config for production
│   ├── urls.py                     # Root URL router
│   └── settings/
│       ├── __init__.py
│       ├── base.py                 # Shared settings (all environments)
│       ├── development.py           # Development-specific settings
│       └── production.py            # Production-specific settings
│
├── apps/                            # Django applications
│   ├── __init__.py
│   │
│   ├── accounts/                   # User authentication & profiles
│   │   ├── __init__.py
│   │   ├── admin.py                # Django admin configuration
│   │   ├── apps.py                 # App config
│   │   ├── forms.py                # Login, register, profile forms
│   │   ├── managers.py             # CustomUserManager for email auth
│   │   ├── models.py               # CustomUser model (email-based auth)
│   │   ├── serializers.py          # DRF serializers for API
│   │   ├── tests.py                # Unit tests
│   │   ├── urls.py                 # Account routes
│   │   ├── views.py                # Login, register, profile views
│   │   └── migrations/
│   │       ├── __init__.py
│   │       └── 0001_initial.py
│   │
│   ├── complaints/                 # Core complaint management
│   │   ├── __init__.py
│   │   ├── admin.py                # Complaint admin interface
│   │   ├── apps.py                 # App config
│   │   ├── forms.py                # ComplaintForm, ComplaintImageForm
│   │   ├── models.py               # Complaint, ComplaintImage, StatusUpdate, ComplaintForwardLog
│   │   ├── serializers.py          # DRF serializers for API
│   │   ├── signals.py              # Auto-generate tracking IDs, trigger notifications
│   │   ├── tests.py                # Unit tests for complaint CRUD
│   │   ├── urls.py                 # Complaint routes (/submit, /list, /track, /detail)
│   │   ├── views.py                # ComplaintListView, ComplaintDetailView, ComplaintSubmitView
│   │   └── migrations/
│   │       ├── __init__.py
│   │       ├── 0001_initial.py
│   │       └── 0002_alter_complaint_status_...py
│   │
│   ├── departments/                # Government department management
│   │   ├── __init__.py
│   │   ├── admin.py                # Department admin interface
│   │   ├── apps.py                 # App config
│   │   ├── forms.py                # DepartmentForm, DepartmentSettingsForm
│   │   ├── models.py               # Department, DepartmentStaff models
│   │   ├── serializers.py          # DRF serializers for API
│   │   ├── tests.py                # Unit tests
│   │   ├── urls.py                 # Department routes
│   │   ├── views.py                # Department detail, settings, staff management
│   │   └── migrations/
│   │       ├── __init__.py
│   │       └── 0001_initial.py
│   │
│   ├── notifications/              # Email & SMS notification system
│   │   ├── __init__.py
│   │   ├── admin.py                # Notification logs admin
│   │   ├── apps.py                 # App config
│   │   ├── models.py               # NotificationLog, EmailTemplate models
│   │   ├── services.py             # send_email_notification(), send_sms_notification()
│   │   ├── tests.py                # Unit tests
│   │   ├── urls.py                 # Notification routes
│   │   ├── views.py                # Notification preference views
│   │   └── migrations/
│   │       ├── __init__.py
│   │       └── 0001_initial.py
│   │
│   └── ai_engine/                  # AI classification & routing
│       ├── __init__.py
│       ├── apps.py                 # App config
│       ├── classifier.py           # classify_complaint() using Groq API
│       ├── router.py               # route_complaint() to departments
│       ├── tests.py                # Unit tests for AI logic
│       ├── urls.py                 # AI engine routes
│       ├── utils.py                # Utility functions (priority scoring, keyword matching)
│       ├── views.py                # API endpoints for classification
│       └── migrations/
│           └── __init__.py
│
├── services/                        # Cross-app business logic
│   ├── __init__.py
│   └── complaint_service.py        # Orchestrates: complaint creation → AI classification → routing → notifications
│
├── templates/                       # HTML templates (Jinja2)
│   ├── base.html                   # Base template with navbar, footer
│   ├── home.html                   # Landing page / home dashboard
│   ├── footer.html                 # Footer component
│   ├── navbar.html                 # Navigation bar component
│   │
│   ├── accounts/
│   │   ├── login.html              # Citizen login page
│   │   ├── register.html           # Citizen registration page
│   │   ├── department_login.html   # Department staff login page
│   │   ├── department_register.html # Department staff registration page
│   │   └── profile.html            # User profile page
│   │
│   ├── complaints/
│   │   ├── submit.html             # Submit complaint form
│   │   ├── list.html               # Complaints list (paginated, filterable)
│   │   ├── public_list.html        # Public complaints list (anonymous view)
│   │   ├── detail.html             # Complaint detail with status timeline
│   │   ├── track.html              # Public complaint tracker (by tracking ID)
│   │   ├── map.html                # Interactive map of complaints
│   │   ├── staff_queue.html        # Department staff complaint queue
│   │   └── staff_review.html       # Staff review & update complaint
│   │
│   └── dashboard/
│       └── admin_dashboard.html    # Admin analytics dashboard
│
├── static/                          # Static assets (CSS, JS, images)
│   ├── css/
│   │   └── styles.css              # Global stylesheets (Tailwind CSS)
│   ├── js/
│   │   └── main.js                 # JavaScript utilities, AJAX handlers
│   └── images/
│       └── (logos, icons, etc.)
│
├── media/                           # User-uploaded files
│   ├── complaints/
│   │   └── images/                 # Complaint images organized by year/month
│   │       └── 2026/
│   │           └── 05/
│   └── profiles/                    # User profile pictures
│
├── requirements/                    # Pip dependencies by environment
│   ├── base.txt                    # Shared dependencies (all environments)
│   ├── dev.txt                     # Development-specific (includes base.txt)
│   └── prod.txt                    # Production-specific (includes base.txt)
│
├── manage.py                        # Django CLI tool
├── db.sqlite3                       # SQLite database (development only)
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
├── LICENSE                          # MIT License
├── README.md                        # This file
└── test_twilio.py                  # Twilio SMS testing script
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.10+**
- **pip** (Python package manager)
- **Git**
- **Twilio Account** (for SMS notifications)
- **Groq API Key** (for AI classification)
- **Email Service** (Gmail SMTP or custom)

### Installation & Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/ai-complaint-system.git
cd ai-complaint-system
```

#### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies
```bash
# Development environment
pip install -r requirements/dev.txt

# Production environment
pip install -r requirements/prod.txt
```

#### 4. Setup Environment Variables
```bash
# Copy the template
cp .env.example .env

# Edit .env with your values:
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3

# Groq API for AI classification
GROQ_API_KEY=your-groq-api-key

# Twilio SMS notifications
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# Email configuration
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@complaintSystem.com
```

#### 5. Run Migrations & Start Server
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## 🔌 API Endpoints (REST Framework)

### Authentication
- `POST /api/token/` - Obtain authentication token
- `POST /api/token/refresh/` - Refresh token

### Complaints
- `GET /api/complaints/` - List all complaints (paginated)
- `POST /api/complaints/` - Create new complaint
- `GET /api/complaints/<id>/` - Get complaint details
- `PUT /api/complaints/<id>/` - Update complaint
- `PATCH /api/complaints/<id>/` - Partial update
- `DELETE /api/complaints/<id>/` - Delete complaint

### Departments
- `GET /api/departments/` - List departments
- `POST /api/departments/` - Create department
- `GET /api/departments/<id>/` - Get department details

### Users
- `GET /api/users/` - List users
- `POST /api/users/register/` - Register new user
- `GET /api/users/<id>/` - Get user profile

### AI Classification
- `POST /api/ai/classify/` - Classify complaint text/image

---



## 📚 Key Models

### CustomUser
- Email-based authentication (not username)
- Role-based (Citizen, Department Staff, Admin)
- Profile picture, phone, address fields

### Complaint
- Unique tracking ID (public identifier)
- Text + image support
- AI-assigned category and confidence score
- Multi-status lifecycle
- Geolocation coordinates
- Priority levels (Low → Critical)

### Department
- Manages complaint categories
- Linked to staff users
- Contact information
- Active/inactive toggle

### StatusUpdate
- Audit trail of all status changes
- Timestamps for each update
- Notes/comments field

### ComplaintImage
- Multiple images per complaint
- Organized media structure

### NotificationLog
- Email and SMS delivery tracking
- Retry mechanism

---

## 🔐 Security Features

✅ **CSRF Protection** - Django's built-in CSRF middleware  
✅ **SQL Injection Prevention** - ORM-based queries  
✅ **Password Hashing** - Django's PBKDF2 password hashing  
✅ **Secret Management** - Environment variables  
✅ **HTTPS Ready** - Production-ready security settings  
✅ **CORS Configuration** - Controlled cross-origin access  
✅ **Rate Limiting** - Ready for DRF throttling  
✅ **Email Verification** - Built-in user verification  

---

## 🚢 Deployment

### Development
```bash
python manage.py runserver
```

### Production
```bash
# Collect static files
python manage.py collectstatic --noinput

# Run with Gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000

# Use environment-specific settings
export DJANGO_SETTINGS_MODULE=config.settings.production
```

### Environment Configuration
- **Development:** SQLite, DEBUG=True, local SMTP
- **Production:** PostgreSQL, DEBUG=False, email service provider

---

## 📞 Support & Contact

### Environment Variables Needed
```
DJANGO_SECRET_KEY
DJANGO_DEBUG
DATABASE_URL
GROQ_API_KEY
TWILIO_ACCOUNT_SID
TWILIO_AUTH_TOKEN
TWILIO_PHONE_NUMBER
EMAIL_HOST_USER
EMAIL_HOST_PASSWORD
```

### Troubleshooting


---

**Built with ❤️ for citizen empowerment and transparent governance.**
