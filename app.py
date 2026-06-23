from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, jsonify
from flask_session import Session
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import string
import random
from datetime import datetime
from functools import wraps

app = Flask(__name__)

# Configuration
app.secret_key = 'your-secret-key-change-this-in-production'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max file size
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

Session(app)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Context processor to add unread messages count to all templates
@app.context_processor
def inject_unread_messages():
    unread_messages = 0
    if 'user_id' in session:
        conn = get_db_connection()
        if session.get('role') == 'Admin':
            # Count unread messages for admin
            unread_messages = conn.execute('''
                SELECT COUNT(*) as count FROM messages 
                WHERE receiver_id = ? AND is_read = 0
            ''', (session['user_id'],)).fetchone()['count']
        else:
            # Count unread messages for user from admin
            admin = conn.execute('SELECT * FROM users WHERE role = ?', ('Admin',)).fetchone()
            if admin:
                unread_messages = conn.execute('''
                    SELECT COUNT(*) as count FROM messages 
                    WHERE receiver_id = ? AND sender_id = ? AND is_read = 0
                ''', (session['user_id'], admin['id'])).fetchone()['count']
        conn.close()
    return dict(unread_messages=unread_messages)

# Database connection
def get_db_connection():
    conn = sqlite3.connect('database/lostfound.db')
    conn.row_factory = sqlite3.Row
    return conn

# Initialize database
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create items table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            name TEXT NOT NULL,
            location TEXT NOT NULL,
            date TEXT NOT NULL,
            reporter TEXT NOT NULL,
            email TEXT,
            status TEXT DEFAULT 'Lost',
            notes TEXT,
            user_id INTEGER,
            image TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create audits table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            action TEXT NOT NULL,
            admin TEXT NOT NULL,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES items (id)
        )
    ''')
    
    # Create categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create claims table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS claims (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (item_id) REFERENCES items (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Create notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            target TEXT DEFAULT 'all',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users (id),
            FOREIGN KEY (receiver_id) REFERENCES users (id)
        )
    ''')
    
    # Create default admin user if not exists
    cursor.execute('SELECT * FROM users WHERE email = ?', ('admin@school.edu',))
    admin_user = cursor.fetchone()
    if not admin_user:
        cursor.execute('''
            INSERT INTO users (name, email, password, role)
            VALUES (?, ?, ?, ?)
        ''', ('Admin', 'admin@school.edu', generate_password_hash('admin123'), 'Admin'))
    elif not admin_user['password'] or admin_user['password'] == '':
        # Update admin user if password is empty or invalid
        cursor.execute('''
            UPDATE users SET password = ? WHERE email = ?
        ''', (generate_password_hash('admin123'), 'admin@school.edu'))
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# Helper functions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'Admin':
            flash('Access denied. Admin only.', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    # Get real statistics for landing page
    conn = get_db_connection()
    
    total_users = conn.execute('SELECT COUNT(*) as count FROM users WHERE role != ?', ('Admin',)).fetchone()['count']
    total_items = conn.execute('SELECT COUNT(*) as count FROM items').fetchone()['count']
    returned_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE status IN (?, ?)', ('Claimed', 'Returned')).fetchone()['count']
    found_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE status = ?', ('Found',)).fetchone()['count']
    
    # Calculate recovery rate
    recovery_rate = round((returned_items * 100 / total_items)) if total_items > 0 else 0
    
    conn.close()
    
    return render_template('landing.html',
                          total_users=total_users,
                          total_items=total_items,
                          returned_items=returned_items,
                          found_items=found_items,
                          recovery_rate=recovery_rate)

@app.route('/home')
def home():
    conn = get_db_connection()
    recent_items = conn.execute('SELECT * FROM items ORDER BY created_at DESC LIMIT 6').fetchall()
    conn.close()
    return render_template('index.html', recent_items=recent_items)

@app.route('/browse')
def browse():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('browse.html', items=items)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/item/<int:item_id>')
def item_detail(item_id):
    conn = get_db_connection()
    item = conn.execute('SELECT * FROM items WHERE id = ?', (item_id,)).fetchone()
    conn.close()
    if item:
        return render_template('item-detail.html', item=item)
    else:
        flash('Item not found', 'error')
        return redirect(url_for('browse'))

@app.route('/report', methods=['GET', 'POST'])
@login_required
def report():
    if request.method == 'POST':
        # Check if file was uploaded
        file = request.files.get('image')
        image_filename = None
        
        if file and allowed_file(file.filename):
            image_filename = secure_filename(file.filename)
            # Add timestamp to make filename unique
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name, ext = os.path.splitext(image_filename)
            image_filename = f"item_{timestamp}{ext}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO items (type, name, location, date, reporter, email, status, notes, user_id, image)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            request.form['type'],
            request.form['name'],
            request.form['location'],
            request.form['date'],
            request.form['reporter'],
            request.form.get('email', ''),
            request.form['status'],
            request.form.get('notes', ''),
            session['user_id'],
            image_filename
        ))
        conn.commit()
        conn.close()
        
        flash('Item reported successfully!', 'success')
        return redirect(url_for('browse'))
    
    # Get real statistics for the report page
    conn = get_db_connection()
    total_items = conn.execute('SELECT COUNT(*) as count FROM items').fetchone()['count']
    found_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE status = ?', ('Found',)).fetchone()['count']
    claimed_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE status IN (?, ?)', ('Claimed', 'Returned')).fetchone()['count']
    
    # Calculate success rate (claimed + returned / total)
    success_rate = round((claimed_items * 100 / total_items)) if total_items > 0 else 0
    
    conn.close()
    
    return render_template('report.html', 
                          total_items=total_items,
                          found_items=found_items,
                          claimed_items=claimed_items,
                          success_rate=success_rate)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user_type = request.form.get('user_type', 'user')
        
        conn = get_db_connection()
        if user_type == 'admin':
            user = conn.execute('SELECT * FROM users WHERE email = ? AND role = ?', (email, 'Admin')).fetchone()
        else:
            user = conn.execute('SELECT * FROM users WHERE email = ? AND role != ?', (email, 'Admin')).fetchone()
        conn.close()
        
        if user:
            try:
                if check_password_hash(user['password'], password):
                    session['user_id'] = user['id']
                    session['name'] = user['name']
                    session['email'] = user['email']
                    session['role'] = user['role']
                    
                    if user['role'] == 'Admin':
                        return redirect(url_for('admin_dashboard'))
                    else:
                        return redirect(url_for('user_dashboard'))
            except ValueError:
                flash('Invalid password hash. Please contact administrator to reset your password.', 'error')
        else:
            flash('Invalid email or password', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        
        conn = get_db_connection()
        try:
            conn.execute('''
                INSERT INTO users (name, email, password, role)
                VALUES (?, ?, ?, ?)
            ''', (name, email, generate_password_hash(password), role))
            conn.commit()
            conn.close()
            
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            flash('Email already registered', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if session.get('role') == 'Admin':
        return redirect(url_for('admin_dashboard'))
    
    conn = get_db_connection()
    
    # Get user stats
    total_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE user_id = ?', (session['user_id'],)).fetchone()['count']
    lost_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE user_id = ? AND status = ?', (session['user_id'], 'Lost')).fetchone()['count']
    found_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE user_id = ? AND status = ?', (session['user_id'], 'Found')).fetchone()['count']
    claimed_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE user_id = ? AND status = ?', (session['user_id'], 'Claimed')).fetchone()['count']
    
    # Get user's items
    my_items = conn.execute('SELECT * FROM items WHERE user_id = ? ORDER BY created_at DESC LIMIT 10', (session['user_id'],)).fetchall()
    
    # Get recent activity
    recent_activity = conn.execute('SELECT * FROM items ORDER BY created_at DESC LIMIT 5').fetchall()
    
    # Get unread messages count
    admin = conn.execute('SELECT * FROM users WHERE role = ?', ('Admin',)).fetchone()
    unread_messages = 0
    if admin:
        unread_messages = conn.execute('''
            SELECT COUNT(*) as count FROM messages 
            WHERE receiver_id = ? AND sender_id = ? AND is_read = 0
        ''', (session['user_id'], admin['id'])).fetchone()['count']
    
    conn.close()
    
    return render_template('user/dashboard.html', 
                          total_items=total_items, 
                          lost_items=lost_items, 
                          found_items=found_items,
                          claimed_items=claimed_items,
                          my_items=my_items,
                          recent_activity=recent_activity,
                          unread_messages=unread_messages)

@app.route('/user/my-items')
@login_required
def user_my_items():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items WHERE user_id = ? ORDER BY created_at DESC', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('user/my-items.html', items=items)

@app.route('/user/profile')
@login_required
def user_profile():
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    conn.close()
    return render_template('user/profile.html', user=user)

@app.route('/user/profile/update', methods=['POST'])
@login_required
def user_profile_update():
    name = request.form['name']
    email = request.form['email']
    conn = get_db_connection()
    try:
        conn.execute('UPDATE users SET name = ?, email = ? WHERE id = ?', (name, email, session['user_id']))
        conn.commit()
        session['name'] = name
        session['email'] = email
        flash('Profile updated successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('Email already in use.', 'error')
    conn.close()
    return redirect(url_for('user_profile'))

@app.route('/user/my-found-items')
@login_required
def user_my_found_items():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items WHERE user_id = ? AND status IN (?, ?) ORDER BY created_at DESC', (session['user_id'], 'Found', 'Claimed')).fetchall()
    conn.close()
    return render_template('user/my-items.html', items=items, found_items=True)

@app.route('/user/my-claims')
@login_required
def user_my_claims():
    conn = get_db_connection()
    claims = conn.execute('''
        SELECT c.*, i.name as item_name 
        FROM claims c 
        JOIN items i ON c.item_id = i.id 
        WHERE c.user_id = ? 
        ORDER BY c.created_at DESC
    ''', (session['user_id'],)).fetchall()
    conn.close()
    return render_template('user/my-claims.html', claims=claims)

@app.route('/user/messages')
@login_required
def user_messages():
    conn = get_db_connection()
    
    # Get admin user
    admin = conn.execute('SELECT * FROM users WHERE role = ?', ('Admin',)).fetchone()
    
    # Get all messages between user and admin
    messages = conn.execute('''
        SELECT m.*, u.name as sender_name, u.role as sender_role
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE (m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?)
        ORDER BY m.created_at ASC
    ''', (session['user_id'], admin['id'], admin['id'], session['user_id'])).fetchall()
    
    # Mark messages from admin as read
    conn.execute('UPDATE messages SET is_read = 1 WHERE receiver_id = ? AND sender_id = ?', 
                (session['user_id'], admin['id']))
    conn.commit()
    
    # Count unread messages
    unread_count = conn.execute('''
        SELECT COUNT(*) as count FROM messages 
        WHERE receiver_id = ? AND is_read = 0
    ''', (session['user_id'],)).fetchone()['count']
    
    conn.close()
    
    return render_template('user/messages.html', messages=messages, admin=admin, unread_count=unread_count)

@app.route('/user/messages/send', methods=['POST'])
@login_required
def user_send_message():
    message = request.form.get('message')
    
    if not message or not message.strip():
        flash('Message cannot be empty.', 'error')
        return redirect(url_for('user_messages'))
    
    conn = get_db_connection()
    
    # Get admin user
    admin = conn.execute('SELECT * FROM users WHERE role = ?', ('Admin',)).fetchone()
    
    # Insert message
    conn.execute('''
        INSERT INTO messages (sender_id, receiver_id, message)
        VALUES (?, ?, ?)
    ''', (session['user_id'], admin['id'], message.strip()))
    conn.commit()
    conn.close()
    
    flash('Message sent successfully!', 'success')
    return redirect(url_for('user_messages'))

@app.route('/user/notifications')
@login_required
def user_notifications():
    conn = get_db_connection()
    notifications = conn.execute('SELECT * FROM notifications ORDER BY created_at DESC LIMIT 20').fetchall()
    conn.close()
    return render_template('user/notifications.html', notifications=notifications)

@app.route('/user/change-password', methods=['GET', 'POST'])
@login_required
def user_change_password():
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return redirect(url_for('user_change_password'))
        
        if len(new_password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return redirect(url_for('user_change_password'))
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        
        if not check_password_hash(user['password'], current_password):
            conn.close()
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('user_change_password'))
        
        conn.execute('UPDATE users SET password = ? WHERE id = ?', (generate_password_hash(new_password), session['user_id']))
        conn.commit()
        conn.close()
        flash('Password updated successfully!', 'success')
        return redirect(url_for('user_dashboard'))
    
    return render_template('user/change-password.html')

# Admin routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    
    # Get system stats
    total_items = conn.execute('SELECT COUNT(*) as count FROM items').fetchone()['count']
    lost_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE status = ?', ('Lost',)).fetchone()['count']
    found_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE status = ?', ('Found',)).fetchone()['count']
    claimed_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE status = ?', ('Claimed',)).fetchone()['count']
    total_users = conn.execute('SELECT COUNT(*) as count FROM users WHERE role != ?', ('Admin',)).fetchone()['count']
    
    # Get recent items
    recent_items = conn.execute('SELECT * FROM items ORDER BY created_at DESC LIMIT 10').fetchall()
    
    # Get recent activity
    recent_activity = conn.execute('SELECT * FROM items ORDER BY created_at DESC LIMIT 5').fetchall()
    
    # Get unread messages count
    unread_messages = conn.execute('''
        SELECT COUNT(*) as count FROM messages 
        WHERE receiver_id = ? AND is_read = 0
    ''', (session['user_id'],)).fetchone()['count']
    
    conn.close()
    
    return render_template('admin/dashboard.html',
                          total_items=total_items,
                          lost_items=lost_items,
                          found_items=found_items,
                          claimed_items=claimed_items,
                          total_users=total_users,
                          recent_items=recent_items,
                          recent_activity=recent_activity,
                          unread_messages=unread_messages)

@app.route('/admin/items')
@admin_required
def admin_items():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM items ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin/items.html', items=items)

@app.route('/admin/item/<int:item_id>/update', methods=['POST'])
@admin_required
def admin_item_update(item_id):
    status = request.form.get('status')
    conn = get_db_connection()
    conn.execute('UPDATE items SET status = ? WHERE id = ?', (status, item_id))
    
    # Add audit log
    conn.execute('''
        INSERT INTO audits (item_id, action, admin, note)
        VALUES (?, ?, ?, ?)
    ''', (item_id, 'update', session['name'], f'Status changed to {status}'))
    
    conn.commit()
    conn.close()
    flash('Item updated successfully', 'success')
    return redirect(url_for('admin_items'))

@app.route('/admin/item/<int:item_id>/delete', methods=['POST'])
@admin_required
def admin_item_delete(item_id):
    conn = get_db_connection()
    # Get item info for audit
    item = conn.execute('SELECT * FROM items WHERE id = ?', (item_id,)).fetchone()
    
    # Delete item
    conn.execute('DELETE FROM items WHERE id = ?', (item_id,))
    
    # Add audit log
    conn.execute('''
        INSERT INTO audits (item_id, action, admin, note)
        VALUES (?, ?, ?, ?)
    ''', (item_id, 'delete', session['name'], f'Deleted item: {item["name"]}'))
    
    conn.commit()
    conn.close()
    flash('Item deleted successfully', 'success')
    return redirect(url_for('admin_items'))

@app.route('/admin/users')
@admin_required
def admin_users():
    conn = get_db_connection()
    users = conn.execute('SELECT * FROM users WHERE role != ?', ('Admin',)).fetchall()
    conn.close()
    return render_template('admin/users.html', users=users)

@app.route('/admin/audit-log')
@admin_required
def admin_audit_log():
    conn = get_db_connection()
    audits = conn.execute('SELECT * FROM audits ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin/audit-log.html', audits=audits)

@app.route('/admin/found-items')
@admin_required
def admin_found_items():
    conn = get_db_connection()
    items = conn.execute("SELECT * FROM items WHERE status IN ('Found', 'Claimed') ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template('admin/found-items.html', items=items)

@app.route('/admin/claims')
@admin_required
def admin_claims():
    conn = get_db_connection()
    claims = conn.execute('''
        SELECT c.*, i.name as item_name, u.name as claimant_name
        FROM claims c
        JOIN items i ON c.item_id = i.id
        JOIN users u ON c.user_id = u.id
        ORDER BY c.created_at DESC
    ''').fetchall()
    conn.close()
    return render_template('admin/claims.html', claims=claims)

@app.route('/admin/claims/<int:claim_id>/update', methods=['POST'])
@admin_required
def admin_claim_update(claim_id):
    status = request.form.get('status')
    conn = get_db_connection()
    conn.execute('UPDATE claims SET status = ? WHERE id = ?', (status, claim_id))
    conn.commit()
    conn.close()
    flash(f'Claim {status.lower()} successfully.', 'success')
    return redirect(url_for('admin_claims'))

@app.route('/admin/categories', methods=['GET', 'POST'])
@admin_required
def admin_categories():
    conn = get_db_connection()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        try:
            conn.execute('INSERT INTO categories (name, description) VALUES (?, ?)', (name, description))
            conn.commit()
            flash('Category added successfully!', 'success')
        except sqlite3.IntegrityError:
            flash('Category already exists.', 'error')
        conn.close()
        return redirect(url_for('admin_categories'))
    
    categories = conn.execute('SELECT * FROM categories ORDER BY name').fetchall()
    conn.close()
    return render_template('admin/categories.html', categories=categories)

@app.route('/admin/categories/<int:category_id>/delete', methods=['POST'])
@admin_required
def admin_category_delete(category_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM categories WHERE id = ?', (category_id,))
    conn.commit()
    conn.close()
    flash('Category deleted.', 'success')
    return redirect(url_for('admin_categories'))

@app.route('/admin/notifications', methods=['GET', 'POST'])
@admin_required
def admin_notifications():
    conn = get_db_connection()
    if request.method == 'POST':
        title = request.form['title']
        message = request.form['message']
        target = request.form.get('target', 'all')
        conn.execute('INSERT INTO notifications (title, message, target) VALUES (?, ?, ?)', (title, message, target))
        conn.commit()
        conn.close()
        flash('Notification sent!', 'success')
        return redirect(url_for('admin_notifications'))
    
    notifications = conn.execute('SELECT * FROM notifications ORDER BY created_at DESC').fetchall()
    conn.close()
    return render_template('admin/notifications.html', notifications=notifications)

@app.route('/admin/notifications/<int:notification_id>/delete', methods=['POST'])
@admin_required
def admin_notification_delete(notification_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM notifications WHERE id = ?', (notification_id,))
    conn.commit()
    conn.close()
    flash('Notification deleted.', 'success')
    return redirect(url_for('admin_notifications'))

@app.route('/admin/messages')
@admin_required
def admin_messages():
    conn = get_db_connection()
    
    # Get all users (non-admin)
    users = conn.execute('SELECT * FROM users WHERE role != ? ORDER BY name', ('Admin',)).fetchall()
    
    # Get selected user if any
    selected_user_id = request.args.get('user_id', type=int)
    selected_user = None
    messages = []
    
    if selected_user_id:
        selected_user = conn.execute('SELECT * FROM users WHERE id = ?', (selected_user_id,)).fetchone()
        
        # Get messages between admin and selected user
        messages = conn.execute('''
            SELECT m.*, u.name as sender_name, u.role as sender_role
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE (m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?)
            ORDER BY m.created_at ASC
        ''', (session['user_id'], selected_user_id, selected_user_id, session['user_id'])).fetchall()
        
        # Mark messages from user as read
        conn.execute('UPDATE messages SET is_read = 1 WHERE receiver_id = ? AND sender_id = ?', 
                    (session['user_id'], selected_user_id))
        conn.commit()
    
    # Get unread message count for each user
    user_unread = {}
    for user in users:
        count = conn.execute('''
            SELECT COUNT(*) as count FROM messages 
            WHERE sender_id = ? AND receiver_id = ? AND is_read = 0
        ''', (user['id'], session['user_id'])).fetchone()['count']
        user_unread[user['id']] = count
    
    conn.close()
    
    return render_template('admin/messages.html', 
                          users=users, 
                          selected_user=selected_user,
                          messages=messages,
                          user_unread=user_unread)

@app.route('/admin/messages/send', methods=['POST'])
@admin_required
def admin_send_message():
    user_id = request.form.get('user_id', type=int)
    message = request.form.get('message')
    
    if not message or not message.strip():
        flash('Message cannot be empty.', 'error')
        return redirect(url_for('admin_messages', user_id=user_id))
    
    conn = get_db_connection()
    
    # Insert message
    conn.execute('''
        INSERT INTO messages (sender_id, receiver_id, message)
        VALUES (?, ?, ?)
    ''', (session['user_id'], user_id, message.strip()))
    conn.commit()
    conn.close()
    
    flash('Message sent successfully!', 'success')
    return redirect(url_for('admin_messages', user_id=user_id))

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    conn = get_db_connection()
    admin = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'update_profile':
            name = request.form['name']
            email = request.form['email']
            try:
                conn.execute('UPDATE users SET name = ?, email = ? WHERE id = ?', (name, email, session['user_id']))
                conn.commit()
                session['name'] = name
                session['email'] = email
                flash('Profile updated successfully!', 'success')
            except sqlite3.IntegrityError:
                flash('Email already in use.', 'error')
        
        elif action == 'change_password':
            current_password = request.form['current_password']
            new_password = request.form['new_password']
            confirm_password = request.form['confirm_password']
            
            if new_password != confirm_password:
                conn.close()
                flash('New passwords do not match.', 'error')
                return redirect(url_for('admin_settings'))
            
            if not check_password_hash(admin['password'], current_password):
                conn.close()
                flash('Current password is incorrect.', 'error')
                return redirect(url_for('admin_settings'))
            
            conn.execute('UPDATE users SET password = ? WHERE id = ?', (generate_password_hash(new_password), session['user_id']))
            conn.commit()
            flash('Password updated successfully!', 'success')
    
    conn.close()
    return render_template('admin/settings.html', admin=admin)

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        
        if user:
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            conn.execute('UPDATE users SET password = ? WHERE id = ?', (generate_password_hash(temp_password), user['id']))
            conn.commit()
            conn.close()
            return render_template('forgot-password.html', temp_password=temp_password)
        else:
            conn.close()
            flash('No account found with that email address.', 'error')
    
    return render_template('forgot-password.html', temp_password=None)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/reset-admin-password')
def reset_admin_password():
    """Reset admin password to fix invalid hash issue"""
    conn = get_db_connection()
    conn.execute('UPDATE users SET password = ? WHERE email = ?', 
                (generate_password_hash('admin123'), 'admin@school.edu'))
    conn.commit()
    conn.close()
    return 'Admin password has been reset to: admin123'

# API Endpoints for Real-time Statistics
@app.route('/api/stats/global')
def api_global_stats():
    """Get global statistics for all items"""
    conn = get_db_connection()
    
    total_items = conn.execute('SELECT COUNT(*) as count FROM items').fetchone()['count']
    lost_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE status = ?', ('Lost',)).fetchone()['count']
    found_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE status = ?', ('Found',)).fetchone()['count']
    claimed_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE status = ?', ('Claimed',)).fetchone()['count']
    pending_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE status = ?', ('Pending',)).fetchone()['count']
    total_users = conn.execute('SELECT COUNT(*) as count FROM users WHERE role != ?', ('Admin',)).fetchone()['count']
    
    # Calculate recovery rate
    recovery_rate = round((found_items * 100 / total_items)) if total_items > 0 else 0
    
    conn.close()
    
    return jsonify({
        'total_items': total_items,
        'lost_items': lost_items,
        'found_items': found_items,
        'claimed_items': claimed_items,
        'pending_items': pending_items,
        'total_users': total_users,
        'recovery_rate': recovery_rate
    })

@app.route('/api/stats/user')
@login_required
def api_user_stats():
    """Get statistics for logged-in user"""
    conn = get_db_connection()
    
    total_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE user_id = ?', (session['user_id'],)).fetchone()['count']
    lost_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE user_id = ? AND status = ?', (session['user_id'], 'Lost')).fetchone()['count']
    found_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE user_id = ? AND status = ?', (session['user_id'], 'Found')).fetchone()['count']
    claimed_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE user_id = ? AND status = ?', (session['user_id'], 'Claimed')).fetchone()['count']
    
    # Get unread messages count
    admin = conn.execute('SELECT * FROM users WHERE role = ?', ('Admin',)).fetchone()
    unread_messages = 0
    if admin:
        unread_messages = conn.execute('''
            SELECT COUNT(*) as count FROM messages 
            WHERE receiver_id = ? AND sender_id = ? AND is_read = 0
        ''', (session['user_id'], admin['id'])).fetchone()['count']
    
    conn.close()
    
    return jsonify({
        'total_items': total_items,
        'lost_items': lost_items,
        'found_items': found_items,
        'claimed_items': claimed_items,
        'unread_messages': unread_messages
    })

@app.route('/api/stats/admin')
@admin_required
def api_admin_stats():
    """Get statistics for admin dashboard"""
    conn = get_db_connection()
    
    total_items = conn.execute('SELECT COUNT(*) as count FROM items').fetchone()['count']
    lost_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE status = ?', ('Lost',)).fetchone()['count']
    found_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE status = ?', ('Found',)).fetchone()['count']
    claimed_items = conn.execute('SELECT COUNT(*) as count FROM items WHERE status = ?', ('Claimed',)).fetchone()['count']
    pending_claims = conn.execute('SELECT COUNT(*) as count FROM claims WHERE status = ?', ('Pending',)).fetchone()['count']
    total_users = conn.execute('SELECT COUNT(*) as count FROM users WHERE role != ?', ('Admin',)).fetchone()['count']
    
    # Get unread messages count
    unread_messages = conn.execute('''
        SELECT COUNT(*) as count FROM messages 
        WHERE receiver_id = ? AND is_read = 0
    ''', (session['user_id'],)).fetchone()['count']
    
    # Calculate recovery rate
    recovery_rate = round((found_items * 100 / total_items)) if total_items > 0 else 0
    
    conn.close()
    
    return jsonify({
        'total_items': total_items,
        'lost_items': lost_items,
        'found_items': found_items,
        'claimed_items': claimed_items,
        'pending_claims': pending_claims,
        'total_users': total_users,
        'recovery_rate': recovery_rate,
        'unread_messages': unread_messages
    })

@app.route('/api/items/recent')
def api_recent_items():
    """Get recent items activity"""
    limit = request.args.get('limit', 10, type=int)
    conn = get_db_connection()
    
    items = conn.execute('SELECT * FROM items ORDER BY created_at DESC LIMIT ?', (limit,)).fetchall()
    
    items_list = []
    for item in items:
        items_list.append({
            'id': item['id'],
            'name': item['name'],
            'type': item['type'],
            'status': item['status'],
            'location': item['location'],
            'date': item['date'],
            'created_at': item['created_at']
        })
    
    conn.close()
    
    return jsonify({'items': items_list})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
