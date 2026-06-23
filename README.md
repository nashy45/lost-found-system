# Lost & Found Management System

A web-based lost and found management platform built with Flask and SQLite. Designed for school/institutional environments, it allows users to report lost and found items, browse listings, and claim ownership — while administrators manage items, users, claims, categories, and notifications through a full dashboard.

---

## Table of Contents

1. [Features](#features)
2. [Technology Stack](#technology-stack)
3. [Requirements & Installation](#requirements--installation)
4. [Running the Application](#running-the-application)
5. [Default Credentials](#default-credentials)
6. [Project Structure](#project-structure)
7. [Database Schema](#database-schema)
8. [Routes & Endpoints](#routes--endpoints)
9. [Configuration](#configuration)
10. [Security Notes](#security-notes)

---

## Features

### Public (No Login Required)
- **Landing Page** — Introduction, features overview, how-it-works steps, stats, recent items, CTA
- **Browse Items** — View all reported lost and found items
- **Item Details** — View full details of a specific item
- **About Page** — Information about the platform
- **Contact Page** — Contact form / information page
- **Login / Register** — Authentication with role selection (Student/Staff/Faculty)
- **Forgot Password** — Generates a temporary password for account recovery

### User Dashboard (Login Required)
- **Dashboard** — Personal stats (total items, lost, found, claimed), recent activity
- **My Lost Items** — View all items reported as lost
- **My Found Items** — View all items reported as found
- **My Claims** — View status of submitted claims (Pending, Approved, Rejected)
- **Report Item** — Submit a new lost or found item with optional image upload
- **Messages** — Message center
- **Notifications** — View system-wide notifications from admin
- **Profile Settings** — Update name and email
- **Change Password** — Change current password with verification

### Admin Dashboard (Admin Login Required)
- **Dashboard** — System-wide stats, charts (Chart.js), recent items and activity
- **Lost Items** — Manage all items reported as lost (update status, delete)
- **Found Items** — Manage all items reported as found or claimed
- **Claims Management** — Approve or reject user claims on items
- **User Management** — View all registered non-admin users
- **Categories** — Add and manage item categories
- **Audit Log** — View all admin actions on items (update, delete)
- **Notifications** — Send and manage system-wide notifications
- **Settings** — Update admin profile and change password

---

## Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.11+, Flask 3.0.0 |
| **Database** | SQLite 3 |
| **Session Management** | Flask-Session 0.5.0 (filesystem) |
| **Password Hashing** | Werkzeug 3.0.1 (scrypt) |
| **Templates** | Jinja2 (Flask built-in) |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Charts** | Chart.js (admin dashboard) |
| **File Uploads** | Local filesystem (`uploads/` directory) |

---

## Requirements & Installation

### Prerequisites
- **Python 3.11** or higher
- **pip** (Python package manager)

### Step 1: Install Python Dependencies

Open a terminal in the project root directory and run:

```bash
pip install -r requirements.txt
```

This installs the following packages:

| Package | Version | Purpose |
|---|---|---|
| `Flask` | 3.0.0 | Web framework |
| `Flask-Session` | 0.5.0 | Server-side session storage |
| `Werkzeug` | 3.0.1 | Password hashing, file security |

### Step 2: Database Setup

The SQLite database is **automatically created** on first run. The file is located at:

```
database/lostfound.db
```

The database initializes with all required tables and a default admin account.

### Step 3 (Optional): Reset the Database

If you need to reset the database:

```bash
python database/reset.py
```

---

## Running the Application

From the project root directory:

```bash
python app.py
```

The server starts at:
- **Local:** `http://127.0.0.1:5000`
- **Network:** `http://0.0.0.0:5000`

Debug mode is **enabled** by default (auto-reload on code changes).

---

## Default Credentials

| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@school.edu` | `admin123` |

> **Important:** Change the default admin password after first login.

---

## Project Structure

```
lost-found-system/
├── app.py                      # Main Flask application (routes, config, DB init)
├── requirements.txt            # Python dependencies
│
├── database/
│   ├── connection.php          # (Legacy PHP, not used)
│   ├── lostfound.db            # SQLite database file
│   ├── migrate.php             # (Legacy PHP, not used)
│   ├── reset.php               # (Legacy PHP, not used)
│   ├── save_item.php           # (Legacy PHP, not used)
│   └── view_db.php             # (Legacy PHP, not used)
│
├── flask_session/              # Server-side session files (auto-generated)
│
├── static/
│   ├── css/
│   │   ├── admin.css           # Admin dashboard styles
│   │   ├── auth.css            # Login/register/forgot-password styles
│   │   ├── landing.css         # Landing page styles
│   │   ├── style.css           # Global/shared styles
│   │   └── user-dashboard.css  # User dashboard styles
│   ├── images/
│   │   ├── computers.jpg       # Category image
│   │   ├── headphones.jpg      # Category image
│   │   ├── keys.jpg            # Category image
│   │   ├── passport.jpg        # Category image
│   │   ├── phone.jpg           # Category image
│   │   └── wallets.jpg         # Category image
│   └── js/
│       └── script.js           # Global JavaScript
│
├── templates/
│   ├── base.html               # Base template (minimal)
│   ├── landing.html            # Landing page
│   ├── index.html              # Home page with recent items
│   ├── login.html              # Login page
│   ├── register.html           # Registration page
│   ├── forgot-password.html    # Forgot/reset password page
│   ├── browse.html             # Browse all items
│   ├── report.html             # Report lost/found item form
│   ├── item-detail.html        # Single item detail view
│   ├── about.html              # About page
│   ├── contact.html            # Contact page
│   ├── navbar.html             # Shared navigation bar
│   ├── footer.html             # Shared footer
│   │
│   ├── user/                   # User dashboard templates
│   │   ├── base.html           # Shared user sidebar layout
│   │   ├── dashboard.html      # User dashboard home
│   │   ├── my-items.html       # My lost items (also used for found items)
│   │   ├── my-claims.html      # My claims list
│   │   ├── messages.html       # Messages page
│   │   ├── notifications.html  # User notifications
│   │   ├── profile.html        # Profile settings
│   │   └── change-password.html # Change password form
│   │
│   └── admin/                  # Admin dashboard templates
│       ├── base.html           # Shared admin sidebar layout
│       ├── dashboard.html      # Admin dashboard home
│       ├── items.html          # All items (lost) management
│       ├── found-items.html    # Found items management
│       ├── claims.html         # Claims management
│       ├── users.html          # User management
│       ├── categories.html     # Category management
│       ├── audit-log.html      # Audit trail
│       ├── notifications.html  # Send/manage notifications
│       └── settings.html       # Admin profile & password
│
└── uploads/                    # User-uploaded item images
```

---

## Database Schema

### users
Stores user accounts (both regular users and admins).

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER (PK) | Auto-increment user ID |
| `name` | TEXT | Full name |
| `email` | TEXT (UNIQUE) | Email address (used for login) |
| `password` | TEXT | Hashed password (Werkzeug scrypt) |
| `role` | TEXT | User role: `Admin`, `Student`, `Staff`, or `Faculty` |
| `created_at` | TIMESTAMP | Account creation date |

### items
Stores all reported lost and found items.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER (PK) | Auto-increment item ID |
| `type` | TEXT | Item type (e.g., Electronics, Accessories, Documents) |
| `name` | TEXT | Item name |
| `location` | TEXT | Where the item was lost/found |
| `date` | TEXT | Date of loss/discovery |
| `reporter` | TEXT | Name of person reporting |
| `email` | TEXT | Reporter's contact email |
| `status` | TEXT | `Lost`, `Found`, `Pending`, or `Claimed` |
| `notes` | TEXT | Additional description |
| `user_id` | INTEGER (FK) | Reference to users table |
| `image` | TEXT | Uploaded image filename |
| `created_at` | TIMESTAMP | Report creation date |

### claims
Stores user claims on found items.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER (PK) | Auto-increment claim ID |
| `item_id` | INTEGER (FK) | Reference to items table |
| `user_id` | INTEGER (FK) | Reference to users table (claimant) |
| `message` | TEXT | Claim justification message |
| `status` | TEXT | `Pending`, `Approved`, or `Rejected` |
| `created_at` | TIMESTAMP | Claim submission date |

### categories
Admin-managed item categories.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER (PK) | Auto-increment category ID |
| `name` | TEXT (UNIQUE) | Category name |
| `description` | TEXT | Category description |
| `created_at` | TIMESTAMP | Creation date |

### notifications
Admin-sent system notifications.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER (PK) | Auto-increment notification ID |
| `title` | TEXT | Notification title |
| `message` | TEXT | Notification body |
| `target` | TEXT | Audience (`all` by default) |
| `created_at` | TIMESTAMP | Creation date |

### audits
Admin action log for item management.

| Column | Type | Description |
|---|---|---|
| `id` | INTEGER (PK) | Auto-increment audit ID |
| `item_id` | INTEGER (FK) | Reference to items table |
| `action` | TEXT | Action type (`update`, `delete`) |
| `admin` | TEXT | Name of admin who performed the action |
| `note` | TEXT | Action description |
| `created_at` | TIMESTAMP | Action timestamp |

---

## Routes & Endpoints

### Public Routes

| Method | URL | Description |
|---|---|---|
| GET | `/` | Landing page |
| GET | `/home` | Home page with recent items |
| GET | `/browse` | Browse all items |
| GET | `/about` | About page |
| GET | `/contact` | Contact page |
| GET | `/item/<id>` | Item detail view |
| GET/POST | `/login` | User/admin login |
| GET/POST | `/register` | User registration |
| GET/POST | `/forgot-password` | Forgot password (generates temp password) |
| GET | `/logout` | Logout (clears session) |
| GET | `/uploads/<filename>` | Serve uploaded images |
| GET | `/reset-admin-password` | Reset admin password to default |

### User Routes (Login Required)

| Method | URL | Description |
|---|---|---|
| GET | `/user/dashboard` | User dashboard with stats |
| GET | `/user/my-items` | List user's lost items |
| GET | `/user/my-found-items` | List user's found items |
| GET | `/user/my-claims` | List user's claims |
| GET | `/user/messages` | Messages page |
| GET | `/user/notifications` | View notifications |
| GET | `/user/profile` | Profile settings |
| POST | `/user/profile/update` | Update profile (name, email) |
| GET/POST | `/user/change-password` | Change password |
| GET/POST | `/report` | Report a new item |

### Admin Routes (Admin Login Required)

| Method | URL | Description |
|---|---|---|
| GET | `/admin` | Admin dashboard with stats and charts |
| GET | `/admin/items` | Manage all lost items |
| POST | `/admin/item/<id>/update` | Update item status |
| POST | `/admin/item/<id>/delete` | Delete an item |
| GET | `/admin/found-items` | Manage found/claimed items |
| GET | `/admin/claims` | View all claims |
| POST | `/admin/claims/<id>/update` | Approve/reject a claim |
| GET | `/admin/users` | View registered users |
| GET | `/admin/categories` | View categories |
| POST | `/admin/categories` | Add a category |
| POST | `/admin/categories/<id>/delete` | Delete a category |
| GET | `/admin/audit-log` | View admin action log |
| GET | `/admin/notifications` | View notifications |
| POST | `/admin/notifications` | Send a notification |
| POST | `/admin/notifications/<id>/delete` | Delete a notification |
| GET/POST | `/admin/settings` | Admin profile & password settings |

---

## Configuration

All configuration is in `app.py` at the top of the file:

```python
app.secret_key = 'your-secret-key-change-this-in-production'  # Change this!
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024   # 5MB max upload
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
```

| Setting | Default | Description |
|---|---|---|
| `secret_key` | `your-secret-key-...` | Flask secret key — **change in production** |
| `SESSION_TYPE` | `filesystem` | Sessions stored as files in `flask_session/` |
| `UPLOAD_FOLDER` | `uploads` | Directory for user-uploaded images |
| `MAX_CONTENT_LENGTH` | 5MB | Maximum file upload size |
| `ALLOWED_EXTENSIONS` | png, jpg, jpeg, gif | Accepted image formats |

---

## Security Notes

- **Passwords** are hashed using Werkzeug's `generate_password_hash()` (scrypt algorithm). Plain-text passwords are never stored.
- **Sessions** are server-side (Flask-Session), stored on the filesystem — not in browser cookies.
- **File uploads** are sanitized with `secure_filename()` and restricted to image types only.
- **Access control** uses two decorators:
  - `@login_required` — Redirects to login if no active session
  - `@admin_required` — Redirects to login and blocks non-admin users
- **CSRF protection** is not currently implemented — consider adding `Flask-WTF` for production use.
- **The `/reset-admin-password` route is unprotected** — remove or protect it before deploying to production.
- **Debug mode** should be disabled (`debug=False`) in production deployments.

### Production Deployment Recommendations

1. Change `app.secret_key` to a strong random string
2. Set `debug=False` in `app.run()`
3. Use a production WSGI server (e.g., Gunicorn or Waitress)
4. Remove the `/reset-admin-password` route
5. Add CSRF protection via Flask-WTF
6. Use a reverse proxy (Nginx) for static files and SSL termination
7. Configure HTTPS
# School Lost & Found Management System - Flask Version

A modern Lost & Found management system built with Python Flask, designed for schools to help students and staff report and track lost items.

## Features

- **User Authentication**: Login and registration system with role-based access (User/Admin)
- **Item Reporting**: Users can report lost or found items with image uploads
- **Browse & Search**: View all reported items with filtering options
- **User Dashboard**: Track your own reported items and statistics
- **Admin Dashboard**: Manage all items, users, and view audit logs
- **Modern UI**: Clean, responsive design with modern CSS
- **SQLite Database**: Lightweight database for easy deployment

## Tech Stack

- **Backend**: Python Flask 3.0.0
- **Database**: SQLite
- **Session Management**: Flask-Session
- **Authentication**: Werkzeug password hashing
- **Frontend**: Jinja2 templates with modern CSS

## Installation

1. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the Application**
   ```bash
   python app.py
   ```

3. **Access the Application**
   - User Site: http://127.0.0.1:5000
   - Admin Panel: http://127.0.0.1:5000/admin

## Default Credentials

- **Admin**: admin@school.edu / admin123
- **Users**: Register via the registration page
**user names: nadia@gmail.com 
password: nashy12345.

## Project Structure

```
lost-found-system/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/             # Jinja2 templates
│   ├── base.html         # Base template
│   ├── navbar.html       # Navigation bar
│   ├── footer.html       # Footer
│   ├── index.html        # Homepage
│   ├── browse.html       # Browse items
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   ├── report.html       # Report item form
│   ├── item-detail.html  # Item details
│   ├── about.html        # About page
│   ├── contact.html      # Contact page
│   ├── user/             # User-specific templates
│   │   ├── dashboard.html
│   │   ├── my-items.html
│   │   └── profile.html
│   └── admin/            # Admin-specific templates
│       ├── dashboard.html
│       ├── items.html
│       ├── users.html
│       └── audit-log.html
├── static/               # Static assets
│   ├── css/
│   │   └── style.css
│   ├── js/
│   │   └── script.js
│   └── images/
├── uploads/              # Uploaded images
└── database/             # SQLite database
    └── lostfound.db
```

## Usage

### For Users
1. Register an account
2. Log in to access the dashboard
3. Report lost or found items
4. Browse and search for items
5. Track your reported items

### For Admins
1. Log in with admin credentials
2. Access the admin dashboard
3. Manage all reported items
4. Update item status (Lost/Found/Claimed)
5. Manage user accounts
6. View audit logs

## Features Breakdown

### Authentication
- Secure password hashing with Werkzeug
- Session-based authentication
- Role-based access control (User/Admin)
- Protected routes with decorators

### Item Management
- Report items with type, name, location, date, and notes
- Upload images (PNG, JPG, JPEG, GIF, max 5MB)
- Update item status (Lost → Found → Claimed)
- Delete items (Admin only)

### Dashboard
- User dashboard: Personal statistics and recent items
- Admin dashboard: System-wide statistics and management
- Real-time metrics and activity tracking

### Audit Logging
- Track all administrative actions
- Log item updates and deletions
- View complete audit history

## Development

The application runs in debug mode by default. For production deployment:
- Change `app.secret_key` to a secure random key
- Use a production WSGI server (e.g., Gunicorn)
- Set `debug=False` in `app.run()`
- Configure proper file permissions for uploads

## License

This is a final-year project for educational purposes.
