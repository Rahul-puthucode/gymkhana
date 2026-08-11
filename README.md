# GYMKHANA — Gym Management, Workout & Diet Tracking System

GYMKHANA is a full-featured, professional web application designed as an MCA Major Project. It provides a complete, production-grade platform for gym administrators, certified personal trainers, and gym members.

---

## 🌟 Key Features

### 👤 Member Portal
- **Dashboard**: Personal welcome banner, active membership status card with remaining days countdown, current BMI category, today's workout schedule completion rate, and daily calorie macro target tracking.
- **Gym Membership**: Explore available subscription plans (Monthly, Quarterly, Half-Yearly, Yearly VIP), subscribe/renew instantly, and view payment log history.
- **Personalized Workout Management**: Daily exercise checklist with sets, reps, weight targets, and rest intervals. Record actual lifted weight and reps, and calculate completion rates in real time.
- **Personalized Diet Management**: Customized daily nutrition plans with calorie and macro targets (Protein, Carbs, Fat) broken down into Breakfast, Mid-morning, Lunch, Evening snack, and Dinner.
- **Fitness & BMI Progress Analytics**: Log weight, height, chest, waist, arms, and thighs measurements. Dynamic interactive **Chart.js** graphs show weight progression and BMI category trends.
- **Gym Branch Finder**: Interactive **Leaflet.js** map with OpenStreetMap tiles, browser HTML5 geolocation, Haversine formula distance calculation ("X.X km away"), and turn-by-turn map directions.
- **In-App Notifications**: Real-time navbar bell dropdown with unread badge count for subscription expiry warnings, workout/diet plan updates, and announcements.

### 🏋️ Trainer Portal
- **Dashboard**: Overview of assigned athletes, active membership counts, active workout/diet plans, and real-time member progress log.
- **My Members**: Searchable directory of assigned members with quick access to full athlete profiles.
- **Member Detail & Plan Builder**: Complete view of member stats, BMI, subscription status, and interactive forms to assign custom multi-day workout routines and daily meal plans.
- **Progress Monitoring**: View member measurement history over time to adjust fitness regimes.

### 🛡️ Admin Portal
- **Dashboard**: High-level KPI metrics (Total Members, Total Trainers, Active Subscriptions, Expiring Soon Subscriptions, Total Revenue, Total Branches) with Chart.js distribution charts.
- **User Management**: View, search, filter, activate/deactivate, and delete user accounts.
- **Trainer Management**: Create trainer profiles with specializations, experience, and qualifications.
- **Membership Plan Management**: Create and manage subscription plans, change duration, pricing, and benefits.
- **Gym Branch Management**: Add/edit/delete branch locations with map coordinates (Latitude, Longitude), operating hours, and facilities.
- **Reporting Module**: Membership, User, and Fitness progress reports with status filtering, printable layout, and direct **CSV Export** downloads.
- **Activity Audit Logs**: Complete system action tracking (Logins, Registration, Subscriptions, Plan Assignments, User Status Changes).

---

## 🛠️ Technology Stack

- **Frontend**: HTML5, CSS3 (Vanilla Custom Gym SaaS Design System), JavaScript (ES6), Bootstrap 5, Bootstrap Icons, **Chart.js**, **Leaflet.js / OpenStreetMap**.
- **Backend**: Python 3.11, **Flask** (Flask Blueprints modular architecture), Werkzeug Security.
- **Database**: **MySQL** (`mysql.connector` / `schema.sql`) with universal parameterization. Seamless built-in fallback for zero-setup execution.
- **Architecture**: Modular Flask Blueprints (`auth`, `member`, `trainer`, `admin`, `subscription`, `workout`, `diet`, `progress`, `gym`, `notification`, `reports`).

---

## 🚀 Quick Setup & Installation Guide

### 1. Prerequisites
- Python 3.8+
- MySQL Server (optional; application will connect to MySQL or run with embedded fallback automatically)

### 2. Clone / Workspace Location
Navigate to the project root directory:
```bash
cd C:\Users\RAHUL\.gemini\antigravity\scratch\gymkhana
```

### 3. Install Dependencies
```bash
pip install Flask mysql-connector-python python-dotenv Werkzeug python-dateutil
```

### 4. Database Setup & Seeding
Initialize database schema and populate complete demo data (Users, Trainers, Members, Plans, Branches, Exercises, Sample Workouts, Sample Diets):
```bash
python seed.py
```

### 5. Launch the Application
Run the Flask server:
```bash
python app.py
```

Open your browser and navigate to:
```
http://127.0.0.1:5000/
```

---

## 🔑 Demo Credentials

| Role | Email Address | Password | Description |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@gymkhana.com` | `Admin@123` | Full system control, branch CRUD, user management & CSV reports |
| **Trainer 1** | `trainer1@gymkhana.com` | `Trainer@123` | Strength & Conditioning Specialist |
| **Trainer 2** | `trainer2@gymkhana.com` | `Trainer@123` | Weight Loss & Nutrition Specialist |
| **Member 1** | `member1@gymkhana.com` | `Member@123` | Rahul Sharma (Active Subscription, Assigned Workout & Diet) |
| **Member 2** | `member2@gymkhana.com` | `Member@123` | Anita Roy (Active Subscription, Weight Loss Progress) |

---

## 📂 Project Structure

```
gymkhana/
│
├── app.py                     # Main Flask application entry point
├── config.py                  # Application configuration & DB parameters
├── schema.sql                 # MySQL Database Schema (16 tables)
├── seed.py                    # Seed script for initial demo data
├── README.md                  # Project documentation
│
├── routes/                    # Modular Flask Blueprints
│   ├── auth.py                # Registration, Login, Logout, Profile
│   ├── member.py              # Member Dashboard & metrics
│   ├── subscription.py        # Membership plans & active subscriptions
│   ├── workout.py             # Exercise database & workout tracking
│   ├── diet.py                # Diet plans & nutrition breakdown
│   ├── progress.py            # Weight, BMI & body measurement tracking
│   ├── gym.py                 # Branch finder & Leaflet.js map API
│   ├── notification.py        # In-app notifications & unread counter
│   ├── trainer.py             # Trainer portal, member assignment & plan builder
│   ├── admin.py               # Admin portal, user/trainer/plan/branch CRUD
│   └── reports.py             # System reports & CSV exports
│
├── static/
│   ├── css/
│   │   └── style.css          # Custom Gym SaaS styling
│   └── js/
│       └── main.js            # Sidebar toggle, notification checks & actions
│
├── templates/
│   ├── base.html              # Master layout template with role sidebar
│   ├── index.html             # Public Landing Page
│   ├── auth/                  # Login, Register, Profile templates
│   ├── member/                # Member views (Dashboard, Workout, Diet, Progress, Map, Subscriptions)
│   ├── trainer/               # Trainer views (Dashboard, My Members, Member Detail, Plan Builders)
│   ├── admin/                 # Admin views (Dashboard, Users, Trainers, Plans, Branches, Reports, Logs)
│   └── errors/                # Custom 403, 404, 500 error pages
│
└── utils/
    ├── auth.py                # Password hashing & @login_required / @role_required
    ├── database.py            # Parameterized SQL database execution helper
    └── helpers.py             # BMI calculator, activity logger & notification helper
```

---

## 👨‍🎓 Major Project Verification & Features Matrix

- [x] **Authentication**: Password hashing (`werkzeug.security`), session handling, duplicate email prevention.
- [x] **Authorization**: Role-based access control (`@role_required('MEMBER', 'TRAINER', 'ADMIN')`).
- [x] **Subscriptions**: Dynamic remaining days calculation, status badges, payment history.
- [x] **Workouts**: Day-wise workout split, target sets/reps/weight, actual logging, completion %.
- [x] **Diet**: Daily calorie & macro target tracking, meal breakdown with nutrition math.
- [x] **Fitness Progress**: BMI calculation ($BMI = Weight / Height^2$), category badge, Chart.js progress graphs.
- [x] **Gym Geolocation**: Leaflet OpenStreetMap canvas, browser location query, Haversine distance, turn-by-turn directions.
- [x] **Notifications**: In-app bell dropdown with live unread badge count.
- [x] **Admin Operations**: User CRUD, Trainer CRUD, Plan CRUD, Branch CRUD, Activity Logs, CSV Exports.
