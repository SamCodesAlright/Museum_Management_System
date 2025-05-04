from flask import Flask, render_template, request, redirect, url_for, session
from flask_wtf.csrf import CSRFProtect, generate_csrf
import re
import sqlite3
from sqlite3 import Error
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder='static')
app.secret_key = os.getenv('SECRET_KEY')  # Required for session management
csrf = CSRFProtect(app)  # Enable CSRF protection

# Ensure the instance folder exists
INSTANCE_FOLDER = os.path.join(app.root_path, 'instance')
if not os.path.exists(INSTANCE_FOLDER):
    os.makedirs(INSTANCE_FOLDER)

# SQLite database file (stored in the instance folder)
DATABASE = os.path.join(INSTANCE_FOLDER, 'museum.db')

# Regular expressions for validation
EMAIL_REGEX = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
PASSWORD_REGEX = r'^(?=.*\d)(?=.*[!@#$%^&*])(?=.*[a-zA-Z]).{8,}$'

# Database connection and initialization functions
def create_connection():
    """Create a connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DATABASE)
        print(f"Connected to SQLite database: {DATABASE}")
    except Error as e:
        print(f"Error connecting to database: {e}")
    return conn


def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = create_connection()
    if conn is not None:
        try:
            cursor = conn.cursor()

            # List of table creation SQL statements
            tables = [
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    phone_number TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL,
                    address_line1 TEXT NOT NULL,
                    address_line2 TEXT,
                    city TEXT NOT NULL,
                    zip_code TEXT NOT NULL
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS admins (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password TEXT NOT NULL
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS exhibitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exhibit_name TEXT NOT NULL,
                    location TEXT NOT NULL,
                    category TEXT NOT NULL,
                    image_filename TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    opening_time TEXT NOT NULL,
                    closing_time TEXT NOT NULL,
                    description TEXT
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    item_name TEXT NOT NULL,
                    category TEXT NOT NULL,
                    origin TEXT NOT NULL,
                    historical_period TEXT NOT NULL,
                    location TEXT NOT NULL,
                    image_filename TEXT NOT NULL,
                    description TEXT,
                    category_desc TEXT
                )
                """,
                """
                CREATE TABLE IF NOT EXISTS exhibition_objects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    creator TEXT NOT NULL,
                    culture TEXT,
                    date TEXT NOT NULL,
                    medium TEXT,
                    dimensions TEXT,
                    credit TEXT NOT NULL,
                    description TEXT,
                    image_filename TEXT NOT NULL
                )
                """
            ]

            # Execute all table creation statements
            for table_sql in tables:
                cursor.execute(table_sql)
            
            conn.commit()
            print("Database tables created successfully.")
        except Error as e:
            print(f"Error initializing database: {e}")
            conn.rollback()  # Rollback in case of error
        finally:
            conn.close()
    else:
        print("Error: Cannot create database connection.")

# Initialize the database when the app starts
init_db()


@app.route('/register', methods=['GET', 'POST'])
def register():
    errors = {}
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone_number = request.form.get('phone_number')
        email_id = request.form.get('email_id')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        address_line1 = request.form.get('address_line1')
        address_line2 = request.form.get('address_line2')
        city = request.form.get('city')
        zip_code = request.form.get('zip_code')

        # Validating the fields
        if not first_name:
            errors['first_name'] = 'First name is required.'
        if not last_name:
            errors['last_name'] = 'Last name is required.'
        if not phone_number:
            errors['phone_number'] = 'Phone number is required.'
        if not email_id:
            errors['email_id'] = 'Email is required.'
        elif not re.match(EMAIL_REGEX, email_id):
            errors['email_id'] = 'Please enter a valid email address.'
        if not password:
            errors['password'] = 'Password is required.'
        elif not re.match(PASSWORD_REGEX, password):
            errors['password'] = 'Password must be at least 8 characters long and contain at least one number and one special character.'
        if not confirm_password:
            errors['confirm_password'] = 'Confirm password is required.'
        elif password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match.'
        if not address_line1:
            errors['address_line1'] = 'Address Line 1 is required.'
        if not city:
            errors['city'] = 'City is required.'
        if not zip_code:
            errors['zip_code'] = 'Zip code is required.'

        # If no errors, proceed with the registration logic
        if not errors:
            conn = None
            cursor = None
            try:
                # Hash the password using the default method (pbkdf2:sha256)
                hashed_password = generate_password_hash(password)

                # Connect to the SQLite database
                conn = create_connection()
                cursor = conn.cursor()

                # Insert user data into the database
                query = """
                INSERT INTO users (first_name, last_name, phone_number, email, password, address_line1, address_line2, city, zip_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                values = (first_name, last_name, phone_number, email_id, hashed_password, address_line1, address_line2, city, zip_code)
                cursor.execute(query, values)

                # Commit the transaction
                conn.commit()

                # Redirect to the login page after successful registration
                return redirect(url_for('login'))

            except sqlite3.IntegrityError as e:
                errors['database'] = 'Email already exists.'
            except Error as err:
                errors['database'] = f"An error occurred: {err}"
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()

    # Render the registration template with errors (if any)
    return render_template('register.html', errors=errors)

@app.route('/login', methods=['GET', 'POST'])
def login():
    errors = {}
    if request.method == 'POST':
        # Get form data from the login template
        email = request.form.get('email')
        password = request.form.get('password')

        # Validating the email
        if not email:
            errors['email'] = 'Email is required.'
        elif not re.match(EMAIL_REGEX, email):
            errors['email'] = 'Please enter a valid email address.'

        # Validating the password
        if not password:
            errors['password'] = 'Password is required.'

        # If no errors, proceeding with login logic
        if not errors:
            conn = create_connection()
            cursor = conn.cursor()

            # Fetch the user's hashed password from the database
            cursor.execute("SELECT password FROM users WHERE email = ?", (email,))
            user = cursor.fetchone()

            if user and check_password_hash(user[0], password):
                # Password is correct, proceed with login
                session['user_email'] = email
                return redirect(url_for('home'))
            else:
                errors['login'] = 'Invalid email or password.'

            cursor.close()
            conn.close()

    # Render the login template with errors (if any)
    return render_template('login.html', errors=errors)

@app.route('/logout')
def logout():
    session.pop('user_email', None)  
    return redirect(url_for('home'))

@app.route('/adminRegister', methods=['GET', 'POST'])
def adminRegister():
    errors = {}
    if request.method == 'POST':
        # Get form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Validating the fields
        if not first_name:
            errors['first_name'] = 'First name is required.'
        if not last_name:
            errors['last_name'] = 'Last name is required.'
        if not email:
            errors['email'] = 'Email is required.'
        elif not re.match(EMAIL_REGEX, email):
            errors['email'] = 'Please enter a valid email address.'
        if not password:
            errors['password'] = 'Password is required.'
        elif not re.match(PASSWORD_REGEX, password):
            errors['password'] = 'Password must be at least 8 characters long and contain at least one number and one special character.'
        if not confirm_password:
            errors['confirm_password'] = 'Confirm password is required.'
        elif password != confirm_password:
            errors['confirm_password'] = 'Passwords do not match.'

        # If no errors, proceed with the registration logic
        if not errors:
            conn = None
            cursor = None
            try:
                # Hash the password using the default method (pbkdf2:sha256)
                hashed_password = generate_password_hash(password)

                # Connect to the SQLite database
                conn = create_connection()
                cursor = conn.cursor()

                # Insert admin data into the database
                query = """
                INSERT INTO admins (first_name, last_name, email, password)
                VALUES (?, ?, ?, ?)
                """
                values = (first_name, last_name, email, hashed_password)
                cursor.execute(query, values)

                # Commit the transaction
                conn.commit()

                # Redirect to the admin login page after successful registration
                return redirect(url_for('adminLogin'))

            except sqlite3.IntegrityError as e:
                errors['database'] = 'Email already exists.'
            except Error as err:
                errors['database'] = f"An error occurred: {err}"
            finally:
                if cursor:
                    cursor.close()
                if conn:
                    conn.close()

    # Render the admin registration template with errors (if any)
    return render_template('adminRegister.html', errors=errors)

@app.route('/adminLogin', methods=['GET', 'POST'])
def adminLogin():
    errors = {}
    if request.method == 'POST':
        # Get form data from the login template
        email = request.form.get('email')
        password = request.form.get('password')

        # Validating the email
        if not email:
            errors['email'] = 'Email is required.'
        elif not re.match(EMAIL_REGEX, email):
            errors['email'] = 'Please enter a valid email address.'

        # Validating the password
        if not password:
            errors['password'] = 'Password is required.'

        # If no errors, proceeding with login logic
        if not errors:
            conn = create_connection()
            cursor = conn.cursor()

            # Fetch the admin's hashed password from the database
            cursor.execute("SELECT password FROM admins WHERE email = ?", (email,))
            admin = cursor.fetchone()

            if admin and check_password_hash(admin[0], password):
                # Password is correct, proceed with login
                session['admin_email'] = email
                return redirect(url_for('adminDashboard'))
            else:
                errors['login'] = 'Invalid email or password.'

            cursor.close()
            conn.close()

    # Render the admin login template with errors (if any)
    return render_template('adminLogin.html', errors=errors)

@app.route('/adminDashboard')
def adminDashboard():
    if 'admin_email' not in session:
        return redirect(url_for('adminLogin'))
    
    conn = create_connection()
    try:
        data = {
            'counts': {
                'exhibitions': 0,
                'events': 0,
                'artifacts': 0,
                'users': 0
            },
            'recent_exhibitions': []
        }
        
        if conn is not None:
            cursor = conn.cursor()
            
            # Debug: Print all distinct categories in exhibitions table
            cursor.execute("SELECT DISTINCT category FROM exhibitions")
            categories = cursor.fetchall()
            # print("Existing categories in exhibitions table:", categories)
            
            # Get event count - let's try different variations
            queries = [
                ('SELECT COUNT(*) FROM exhibitions WHERE category = "Event"', 'Exact match "Event"'),
                ('SELECT COUNT(*) FROM exhibitions WHERE category LIKE "%Event%"', 'Contains "Event"'),
                ('SELECT COUNT(*) FROM exhibitions WHERE LOWER(category) = "event"', 'Lowercase "event"'),
                ('SELECT COUNT(*) FROM exhibitions', 'All exhibitions')
            ]
            
            for query, description in queries:
                cursor.execute(query)
                count = cursor.fetchone()[0]
                if "Event" in description:
                    data['counts']['events'] = count
            
            # Get other counts
            cursor.execute('SELECT COUNT(*) FROM exhibitions WHERE category != "Event"')
            data['counts']['exhibitions'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM artifacts')
            data['counts']['artifacts'] = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM users')
            data['counts']['users'] = cursor.fetchone()[0]
            
            # Get recent exhibitions
            cursor.execute('''
                SELECT id, exhibit_name, location, start_date, end_date, description 
                FROM exhibitions 
                WHERE category != "Event"
                ORDER BY id DESC 
                LIMIT 5
            ''')
            columns = ['id', 'exhibit_name', 'location', 'start_date', 'end_date', 'description']
            data['recent_exhibitions'] = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
    except Error as e:
        print(f"Database error: {e}")
    finally:
        if conn:
            conn.close()
    
    return render_template('adminDashboard.html', 
                         now=datetime.now(),
                         data=data)

@app.route('/adminLogout')
def adminLogout():
    session.pop('admin_email', None)  # Remove the admin's email from the session
    return redirect(url_for('home'))

@app.route('/section_exhibition', methods=['GET', 'POST'])
def section_exhibition():
    if request.method == 'POST':
        # Handle form submission
        exhibit_name = request.form.get('exhibit_name')
        location = request.form.get('location')
        category = request.form.get('category')
        image_filename = request.form.get('image_filename')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        opening_time = request.form.get('opening_time')
        closing_time = request.form.get('closing_time')
        description = request.form.get('description')

        # Insert data into the database
        conn = create_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO exhibitions (exhibit_name, location, category, image_filename, start_date, end_date, opening_time, closing_time, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (exhibit_name, location, category, image_filename, start_date, end_date, opening_time, closing_time, description))
                conn.commit()
                print("Exhibitions data inserted successfully.")
            except Error as e:
                print(f"Error inserting exhibitions data: {e}")
            finally:
                conn.close()

        # Redirect to the same page to refresh the table
        return redirect(url_for('section_exhibition'))

    # Fetch exhibit data for the table
    conn = create_connection()
    exhibitions = []
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibitions")
            exhibitions = cursor.fetchall()  # Fetch all rows from the exhibits table
        except Error as e:
            print(f"Error fetching exhibitions: {e}")
        finally:
            conn.close()

    # Render the template with the form and exhibit data
    return render_template('section_exhibition.html', exhibitions=exhibitions)

@app.route('/delete_exhibition/<int:exhibit_id>', methods=['POST'])
def delete_exhibition(exhibit_id):
    if 'admin_email' not in session:
        return redirect(url_for('adminLogin'))
    
    if request.method == 'POST':
        try:
            conn = create_connection()
            conn.execute('DELETE FROM exhibitions WHERE id = ?', (exhibit_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error deleting exhibition: {e}")
    
    return redirect(url_for('section_exhibition'))

@app.route('/edit_exhibition/<int:exhibit_id>')
def edit_exhibition(exhibit_id):
    if 'admin_email' not in session:
        return redirect(url_for('adminLogin'))
    
    conn = create_connection()
    exhibition = conn.execute('SELECT * FROM exhibitions WHERE id = ?', (exhibit_id,)).fetchone()
    conn.close()
    
    if not exhibition:
        return redirect(url_for('section_exhibition'))
    
    return render_template('edit_exhibition.html', exhibition=exhibition)

@app.route('/update_exhibition/<int:exhibit_id>', methods=['POST'])
def update_exhibition(exhibit_id):
    if 'admin_email' not in session:
        return redirect(url_for('adminLogin'))
    
    if request.method == 'POST':
        # Get all form data
        exhibit_name = request.form['exhibit_name']
        location = request.form['location']
        category = request.form['category']
        image_filename = request.form['image_filename']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        opening_time = request.form['opening_time']
        closing_time = request.form['closing_time']
        description = request.form['description']
        
        try:
            conn = create_connection()
            conn.execute("""
                UPDATE exhibitions 
                SET exhibit_name = ?, location = ?, category = ?, image_filename = ?,
                    start_date = ?, end_date = ?, opening_time = ?, closing_time = ?, description = ?
                WHERE id = ?
            """, (exhibit_name, location, category, image_filename, start_date, end_date,
                 opening_time, closing_time, description, exhibit_id))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating exhibition: {e}")
    
    return redirect(url_for('section_exhibition'))

@app.route('/section_exhibition_objects', methods=['GET', 'POST'])
def section_exhibition_objects():
    if request.method == 'POST':
        # Handle form submission for objects
        title = request.form.get('title')
        creator = request.form.get('creator')
        culture = request.form.get('culture')
        date = request.form.get('date')
        medium = request.form.get('medium')
        dimensions = request.form.get('dimensions')
        credit = request.form.get('credit')
        description = request.form.get('description')
        image_filename = request.form.get('image_filename')

        # Insert data into the database
        conn = create_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO exhibition_objects 
                    (title, creator, culture, date, medium, dimensions, credit, description, image_filename)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (title, creator, culture, date, medium, dimensions, credit, description, image_filename))
                conn.commit()
                print("Exhibition object inserted successfully.")
            except Error as e:
                print(f"Error inserting exhibition object: {e}")
            finally:
                conn.close()

        return redirect(url_for('section_exhibition_objects'))

    # Fetch objects data for the table
    conn = create_connection()
    objects = []
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibition_objects")
            objects = cursor.fetchall()
        except Error as e:
            print(f"Error fetching exhibition objects: {e}")
        finally:
            conn.close()

    return render_template('section_exhibition_objects.html', objects=objects)

@app.route('/delete_exhibition_object/<int:object_id>', methods=['POST'])
def delete_exhibition_object(object_id):
    if 'admin_email' not in session:
        return redirect(url_for('adminLogin'))
    
    if request.method == 'POST':
        try:
            conn = create_connection()
            conn.execute('DELETE FROM exhibition_objects WHERE id = ?', (object_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error deleting exhibition object: {e}")
    
    return redirect(url_for('section_exhibition_objects'))

@app.route('/edit_exhibition_object/<int:object_id>')
def edit_exhibition_object(object_id):
    if 'admin_email' not in session:
        return redirect(url_for('adminLogin'))
    
    conn = create_connection()
    object = conn.execute('SELECT * FROM exhibition_objects WHERE id = ?', (object_id,)).fetchone()
    conn.close()
    
    if not object:
        return redirect(url_for('section_exhibition_objects'))
    
    return render_template('edit_exhibition_object.html', object=object)

@app.route('/update_exhibition_object/<int:object_id>', methods=['POST'])
def update_exhibition_object(object_id):
    if 'admin_email' not in session:
        return redirect(url_for('adminLogin'))
    
    if request.method == 'POST':
        # Get all form data
        title = request.form['title']
        creator = request.form['creator']
        culture = request.form['culture']
        date = request.form['date']
        medium = request.form['medium']
        dimensions = request.form['dimensions']
        credit = request.form['credit']
        description = request.form['description']
        image_filename = request.form['image_filename']
        
        try:
            conn = create_connection()
            conn.execute("""
                UPDATE exhibition_objects 
                SET title = ?, creator = ?, culture = ?, date = ?,
                    medium = ?, dimensions = ?, credit = ?, description = ?, image_filename = ?
                WHERE id = ?
            """, (title, creator, culture, date, medium, dimensions, credit, description, image_filename, object_id))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating exhibition object: {e}")
    
    return redirect(url_for('section_exhibition_objects'))

@app.route('/section_artifacts', methods=['GET', 'POST'])
def section_artifacts():
    if request.method == 'POST':
        # Handle form submission
        item_name = request.form.get('item_name')
        category = request.form.get('category')
        origin = request.form.get('origin')
        historical_period = request.form.get('historical_period')
        location = request.form.get('location')
        image_filename = request.form.get('image_filename')
        description = request.form.get('description')
        category_desc = request.form.get('category_desc')

        # Insert data into the database
        conn = create_connection()
        if conn is not None:
            try:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO artifacts (item_name, category, origin, historical_period, location, image_filename, description, category_desc)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (item_name, category, origin, historical_period, location, image_filename, description, category_desc))
                conn.commit()
                print("Artifact data inserted successfully.")
            except Error as e:
                print(f"Error inserting artifact data: {e}")
            finally:
                conn.close()

        # Redirect to the same page to refresh the table
        return redirect(url_for('section_artifacts'))

    # Fetch exhibit data for the table
    conn = create_connection()
    artifacts = []
    if conn is not None:
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM artifacts")
            artifacts = cursor.fetchall()  # Fetch all rows from the artifacts table
        except Error as e:
            print(f"Error fetching artifacts: {e}")
        finally:
            conn.close()

    # Render the template with the form and exhibit data
    return render_template('section_artifacts.html', artifacts=artifacts)

@app.route('/edit_artifact/<int:artifact_id>')
def edit_artifact(artifact_id):
    if 'admin_email' not in session:
        return redirect(url_for('adminLogin'))
    
    conn = create_connection()
    artifact = conn.execute('SELECT * FROM artifacts WHERE id = ?', (artifact_id,)).fetchone()
    conn.close()
    
    if not artifact:
        return redirect(url_for('section_artifacts'))
    
    return render_template('edit_artifact.html', artifact=artifact)

@app.route('/update_artifact/<int:artifact_id>', methods=['POST'])
def update_artifact(artifact_id):
    if 'admin_email' not in session:
        return redirect(url_for('adminLogin'))
    
    if request.method == 'POST':
        # Get all form data
        item_name = request.form['item_name']
        category = request.form['category']
        origin = request.form['origin']
        historical_period = request.form['historical_period']
        location = request.form['location']
        image_filename = request.form['image_filename']
        description = request.form['description']
        category_desc = request.form['category_desc']
        
        try:
            conn = create_connection()
            conn.execute("""
                UPDATE artifacts 
                SET item_name = ?, category = ?, origin = ?, historical_period = ?,
                    location = ?, image_filename = ?, description = ?, category_desc = ?
                WHERE id = ?
            """, (item_name, category, origin, historical_period,
                 location, image_filename, description, category_desc, artifact_id))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error updating artifact: {e}")
    
    return redirect(url_for('section_artifacts'))

@app.route('/delete_artifact/<int:artifact_id>', methods=['POST'])
def delete_artifact(artifact_id):
    if 'admin_email' not in session:
        return redirect(url_for('adminLogin'))
    
    if request.method == 'POST':
        try:
            conn = create_connection()
            conn.execute('DELETE FROM artifacts WHERE id = ?', (artifact_id,))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error deleting artifact: {e}")
    
    return redirect(url_for('section_artifacts'))


@app.route('/indian_art')
def indian_art():
    conn = create_connection()
    artifacts = []
    if conn is not None:
        try:
            # Configure row_factory to return dictionaries
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM artifacts WHERE category = 'Indian Art'")
            artifacts = cursor.fetchall()
        except Error as e:
            print(f"Error fetching Indian Art artifacts: {e}")
        finally:
            conn.close()
    
    return render_template('indian_art.html', artifacts=artifacts)


@app.route('/asian_art')
def asian_art():
    conn = create_connection()
    artifacts = []
    if conn is not None:
        try:
            # Configure row_factory to return dictionaries
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM artifacts WHERE category = 'Asian Art'")
            artifacts = cursor.fetchall()
        except Error as e:
            print(f"Error fetching Asian Art artifacts: {e}")
        finally:
            conn.close()
    
    return render_template('asian_art.html', artifacts=artifacts)

@app.route('/arms_and_armor')
def arms_and_armor():
    conn = create_connection()
    artifacts = []
    if conn is not None:
        try:
            # Configure row_factory to return dictionaries
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM artifacts WHERE category = 'Arms and Armor'")
            artifacts = cursor.fetchall()
        except Error as e:
            print(f"Error fetching Arms and Armor artifacts: {e}")
        finally:
            conn.close()
    
    return render_template('arms_and_armor.html', artifacts=artifacts)

@app.route('/egyptian_art')
def egyptian_art():
    conn = create_connection()
    artifacts = []
    if conn is not None:
        try:
            # Configure row_factory to return dictionaries
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM artifacts WHERE category = 'Egyptian Art'")
            artifacts = cursor.fetchall()
        except Error as e:
            print(f"Error fetching Egyptian Art artifacts: {e}")
        finally:
            conn.close()
    
    return render_template('egyptian_art.html', artifacts=artifacts)

@app.route('/islamic_art')
def islamic_art():
    conn = create_connection()
    artifacts = []
    if conn is not None:
        try:
            # Configure row_factory to return dictionaries
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM artifacts WHERE category = 'Islamic Art'")
            artifacts = cursor.fetchall()
        except Error as e:
            print(f"Error fetching Islamic Art artifacts: {e}")
        finally:
            conn.close()
    
    return render_template('islamic_art.html', artifacts=artifacts)

@app.route('/european_art')
def european_art():
    conn = create_connection()
    artifacts = []
    if conn is not None:
        try:
            # Configure row_factory to return dictionaries
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM artifacts WHERE category = 'European Art'")
            artifacts = cursor.fetchall()
        except Error as e:
            print(f"Error fetching European Art artifacts: {e}")
        finally:
            conn.close()
    
    return render_template('european_art.html', artifacts=artifacts)

@app.route('/ancient_american_art')
def ancient_american_art():
    conn = create_connection()
    artifacts = []
    if conn is not None:
        try:
            # Configure row_factory to return dictionaries
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM artifacts WHERE category = 'Ancient American Art'")
            artifacts = cursor.fetchall()
        except Error as e:
            print(f"Error fetching Ancient American Art artifacts: {e}")
        finally:
            conn.close()
    
    return render_template('ancient_american_art.html', artifacts=artifacts)

@app.route('/ancient_near_eastern_art')
def ancient_near_eastern_art():
    conn = create_connection()
    artifacts = []
    if conn is not None:
        try:
            # Configure row_factory to return dictionaries
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM artifacts WHERE category = 'Ancient Near Eastern Art'")
            artifacts = cursor.fetchall()
        except Error as e:
            print(f"Error fetching Ancient Near Eastern Art artifacts: {e}")
        finally:
            conn.close()
    
    return render_template('ancient_near_eastern_art.html', artifacts=artifacts)

@app.route('/medieval_art_and_the_cloisters')
def medieval_art_and_the_cloisters():
    conn = create_connection()
    artifacts = []
    if conn is not None:
        try:
            # Configure row_factory to return dictionaries
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM artifacts WHERE category = 'Medieval Art and The Cloisters'")
            artifacts = cursor.fetchall()
        except Error as e:
            print(f"Error fetching Medieval Art and The Cloisters artifacts: {e}")
        finally:
            conn.close()
    
    return render_template('medieval_art_and_the_cloisters.html', artifacts=artifacts)

@app.route('/caspar_david_friedrich')
def caspar_david_friedrich():
    conn = create_connection()
    exhibition = None
    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibitions WHERE exhibit_name = 'Caspar David Friedrich: The Soul of Nature'")
            exhibition = cursor.fetchone()
            
            if exhibition:
                # Convert Row object to dictionary for easier template handling
                exhibition = dict(exhibition)
        except Error as e:
            print(f"Error fetching exhibition: {e}")
        finally:
            conn.close()
    
    return render_template('caspar_david_friedrich.html', exhibition=exhibition)

@app.route('/caspar_david_friedrich/objects')
def exhibit_objects():
    conn = create_connection()
    objects_list = []

    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibition_objects WHERE creator = ?", ('Caspar David Friedrich',))
            objects = cursor.fetchall()
            
            # Convert each row to a dictionary for easier template access
            objects_list = [dict(row) for row in objects]
        except Error as e:
            print(f"Error fetching exhibition objects: {e}")
        finally:
            conn.close()

    return render_template('exhibit_objects.html', objects=objects_list)

@app.route('/monstrous_beauty')
def monstrous_beauty():
    conn = create_connection()
    exhibition = None
    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibitions WHERE exhibit_name = 'Monstrous Beauty: A Feminist Revision of Chinoiserie'")
            exhibition = cursor.fetchone()
            
            if exhibition:
                # Convert Row object to dictionary for easier template handling
                exhibition = dict(exhibition)
        except Error as e:
            print(f"Error fetching exhibition: {e}")
        finally:
            conn.close()
    
    return render_template('monstrous_beauty.html', exhibition=exhibition)

@app.route('/recasting_the_past')
def recasting_the_past():
    conn = create_connection()
    exhibition = None
    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibitions WHERE exhibit_name = 'Recasting The Past: The Art of Chinese Bronzes, 1100-1900'")
            exhibition = cursor.fetchone()
            
            if exhibition:
                # Convert Row object to dictionary for easier template handling
                exhibition = dict(exhibition)
        except Error as e:
            print(f"Error fetching exhibition: {e}")
        finally:
            conn.close()
    
    return render_template('recasting_the_past.html', exhibition=exhibition)

@app.route('/recasting_the_past/objects')
def exhibit_objects3():
    conn = create_connection()
    objects_list = []

    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibition_objects WHERE culture = ?", ('China',))
            objects = cursor.fetchall()
            
            # Convert each row to a dictionary for easier template access
            objects_list = [dict(row) for row in objects]
        except Error as e:
            print(f"Error fetching exhibition objects: {e}")
        finally:
            conn.close()

    return render_template('exhibit_objects3.html', objects=objects_list)

@app.route('/layered_narratives')
def layered_narratives():
    conn = create_connection()
    exhibition = None
    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibitions WHERE exhibit_name = 'Layered Narratives: The Northern Renaissance Gallery'")
            exhibition = cursor.fetchone()
            
            if exhibition:
                # Convert Row object to dictionary for easier template handling
                exhibition = dict(exhibition)
        except Error as e:
            print(f"Error fetching exhibition: {e}")
        finally:
            conn.close()
    
    return render_template('layered_narratives.html', exhibition=exhibition)

@app.route('/layered_narratives/objects')
def exhibit_objects2():
    conn = create_connection()
    objects_list = []

    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibition_objects WHERE creator = ?", ('Layered narratives',))
            objects = cursor.fetchall()
            
            # Convert each row to a dictionary for easier template access
            objects_list = [dict(row) for row in objects]
        except Error as e:
            print(f"Error fetching exhibition objects: {e}")
        finally:
            conn.close()

    return render_template('exhibit_objects2.html', objects=objects_list)

@app.route('/cycladic_art')
def cycladic_art():
    conn = create_connection()
    exhibition = None
    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibitions WHERE exhibit_name = 'Cycladic Art'")
            exhibition = cursor.fetchone()
            
            if exhibition:
                # Convert Row object to dictionary for easier template handling
                exhibition = dict(exhibition)
        except Error as e:
            print(f"Error fetching exhibition: {e}")
        finally:
            conn.close()
    
    return render_template('cycladic_art.html', exhibition=exhibition)

@app.route('/cycladic_art/objects')
def exhibit_objects1():
    conn = create_connection()
    objects_list = []

    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibition_objects WHERE creator = ?", ('Cycladic Art',))
            objects = cursor.fetchall()
            
            # Convert each row to a dictionary for easier template access
            objects_list = [dict(row) for row in objects]
        except Error as e:
            print(f"Error fetching exhibition objects: {e}")
        finally:
            conn.close()

    return render_template('exhibit_objects1.html', objects=objects_list)


@app.route('/art_of_commerce')
def art_of_commerce():
    conn = create_connection()
    exhibition = None
    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibitions WHERE exhibit_name = 'Art of Commerce: Trade Catalogs in Watson Library'")
            exhibition = cursor.fetchone()
            
            if exhibition:
                # Convert Row object to dictionary for easier template handling
                exhibition = dict(exhibition)
        except Error as e:
            print(f"Error fetching exhibition: {e}")
        finally:
            conn.close()
    
    return render_template('art_of_commerce.html', exhibition=exhibition)

@app.route('/colorful_korea')
def colorful_korea():
    conn = create_connection()
    exhibition = None
    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibitions WHERE exhibit_name = 'Colorful Korea: The Lea R. Sneider Collection'")
            exhibition = cursor.fetchone()
            
            if exhibition:
                # Convert Row object to dictionary for easier template handling
                exhibition = dict(exhibition)
        except Error as e:
            print(f"Error fetching exhibition: {e}")
        finally:
            conn.close()
    
    return render_template('colorful_korea.html', exhibition=exhibition)

@app.route('/colorful_korea/objects')
def exhibit_objects4():
    conn = create_connection()
    objects_list = []

    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibition_objects WHERE culture = ?", ('South Korea',))
            objects = cursor.fetchall()
            
            # Convert each row to a dictionary for easier template access
            objects_list = [dict(row) for row in objects]
        except Error as e:
            print(f"Error fetching exhibition objects: {e}")
        finally:
            conn.close()

    return render_template('exhibit_objects4.html', objects=objects_list)

@app.route('/floridas')
def floridas():
    conn = create_connection()
    exhibition = None
    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibitions WHERE exhibit_name = 'Floridas: Anastasia Samoylova and Walker Evans'")
            exhibition = cursor.fetchone()
            
            if exhibition:
                # Convert Row object to dictionary for easier template handling
                exhibition = dict(exhibition)
        except Error as e:
            print(f"Error fetching exhibition: {e}")
        finally:
            conn.close()
    
    return render_template('floridas.html', exhibition=exhibition)

@app.route('/afterlives')
def afterlives():
    conn = create_connection()
    exhibition = None
    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibitions WHERE exhibit_name = 'Afterlives: Contemporary Art in the Byzantine Crypt'")
            exhibition = cursor.fetchone()
            
            if exhibition:
                # Convert Row object to dictionary for easier template handling
                exhibition = dict(exhibition)
        except Error as e:
            print(f"Error fetching exhibition: {e}")
        finally:
            conn.close()
    
    return render_template('afterlives.html', exhibition=exhibition)

@app.route('/embracing_color')
def embracing_color():
    conn = create_connection()
    exhibition = None
    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibitions WHERE exhibit_name = 'Embracing Color: Enamel in Chinese Decorative Arts, 1300–1900'")
            exhibition = cursor.fetchone()
            
            if exhibition:
                # Convert Row object to dictionary for easier template handling
                exhibition = dict(exhibition)
        except Error as e:
            print(f"Error fetching exhibition: {e}")
        finally:
            conn.close()
    
    return render_template('embracing_color.html', exhibition=exhibition)

@app.route('/embracing_color/objects')
def exhibit_objects7():
    conn = create_connection()
    objects_list = []

    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibition_objects WHERE culture = ?", ('Chinese Decoratives',))
            objects = cursor.fetchall()
            
            # Convert each row to a dictionary for easier template access
            objects_list = [dict(row) for row in objects]
        except Error as e:
            print(f"Error fetching exhibition objects: {e}")
        finally:
            conn.close()

    return render_template('exhibit_objects7.html', objects=objects_list)


@app.route('/before_yesterday_we_could_fly')
def before_yesterday_we_could_fly():
    conn = create_connection()
    exhibition = None
    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibitions WHERE exhibit_name = 'Before Yesterday We Could Fly: An Afrofuturist Period Room'")
            exhibition = cursor.fetchone()
            
            if exhibition:
                # Convert Row object to dictionary for easier template handling
                exhibition = dict(exhibition)
        except Error as e:
            print(f"Error fetching exhibition: {e}")
        finally:
            conn.close()
    
    return render_template('before_yesterday_we_could_fly.html', exhibition=exhibition)

@app.route('/before_yesterday_we_could_fly/objects')
def exhibit_objects5():
    conn = create_connection()
    objects_list = []

    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibition_objects WHERE culture = ?", ('Europe',))
            objects = cursor.fetchall()
            
            # Convert each row to a dictionary for easier template access
            objects_list = [dict(row) for row in objects]
        except Error as e:
            print(f"Error fetching exhibition objects: {e}")
        finally:
            conn.close()

    return render_template('exhibit_objects5.html', objects=objects_list)


@app.route('/art_of_native_america')
def art_of_native_america():
    conn = create_connection()
    exhibition = None
    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibitions WHERE exhibit_name = 'Art of Native America: The Charles and Valerie Diker Collection'")
            exhibition = cursor.fetchone()
            
            if exhibition:
                # Convert Row object to dictionary for easier template handling
                exhibition = dict(exhibition)
        except Error as e:
            print(f"Error fetching exhibition: {e}")
        finally:
            conn.close()
    
    return render_template('art_of_native_america.html', exhibition=exhibition)

@app.route('/art_of_native_america/objects')
def exhibit_objects6():
    conn = create_connection()
    objects_list = []

    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibition_objects WHERE culture = ?", ('Native America',))
            objects = cursor.fetchall()
            
            # Convert each row to a dictionary for easier template access
            objects_list = [dict(row) for row in objects]
        except Error as e:
            print(f"Error fetching exhibition objects: {e}")
        finally:
            conn.close()

    return render_template('exhibit_objects6.html', objects=objects_list)


@app.route('/the_new_art')
def the_new_art():
    conn = create_connection()
    exhibition = None
    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibitions WHERE exhibit_name = 'The New Art: American Photography, 1839–1910'")
            exhibition = cursor.fetchone()
            
            if exhibition:
                # Convert Row object to dictionary for easier template handling
                exhibition = dict(exhibition)
        except Error as e:
            print(f"Error fetching exhibition: {e}")
        finally:
            conn.close()
    
    return render_template('the_new_art.html', exhibition=exhibition)


@app.route('/city_and_country')
def city_and_country():
    conn = create_connection()
    exhibition = None
    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibitions WHERE exhibit_name = 'City and Country: Selections from the Department of Drawings and Prints'")
            exhibition = cursor.fetchone()
            
            if exhibition:
                # Convert Row object to dictionary for easier template handling
                exhibition = dict(exhibition)
        except Error as e:
            print(f"Error fetching exhibition: {e}")
        finally:
            conn.close()
    
    return render_template('city_and_country.html', exhibition=exhibition)


@app.route('/arts_of_the_ancient_americans')
def arts_of_the_ancient_americans():
    conn = create_connection()
    exhibition = None
    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibitions WHERE exhibit_name = 'Arts of the Ancient Americas'")
            exhibition = cursor.fetchone()
            
            if exhibition:
                # Convert Row object to dictionary for easier template handling
                exhibition = dict(exhibition)
        except Error as e:
            print(f"Error fetching exhibition: {e}")
        finally:
            conn.close()
    
    return render_template('arts_of_the_ancient_americans.html', exhibition=exhibition)


@app.route('/arts_of_africa')
def arts_of_africa():
    conn = create_connection()
    exhibition = None
    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibitions WHERE exhibit_name = 'Arts of Africa'")
            exhibition = cursor.fetchone()
            
            if exhibition:
                # Convert Row object to dictionary for easier template handling
                exhibition = dict(exhibition)
        except Error as e:
            print(f"Error fetching exhibition: {e}")
        finally:
            conn.close()
    
    return render_template('arts_of_africa.html', exhibition=exhibition)


@app.route('/the_magical_city')
def the_magical_city():
    conn = create_connection()
    exhibition = None
    if conn is not None:
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibitions WHERE exhibit_name = 'The Magical City: George Morrisons New York'")
            exhibition = cursor.fetchone()
            
            if exhibition:
                # Convert Row object to dictionary for easier template handling
                exhibition = dict(exhibition)
        except Error as e:
            print(f"Error fetching exhibition: {e}")
        finally:
            conn.close()
    
    return render_template('the_magical_city.html', exhibition=exhibition)


# Your existing routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/visit')
def visit():
    return render_template('visit.html')

@app.route('/exhibition')
def exhibition():
    return render_template('exhibition.html')

@app.route('/events')
def events():
    conn = create_connection()
    events = []
    if conn is not None:
        try:
            # Configure row_factory to return dictionaries
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM exhibitions WHERE category = 'Events'")
            events = cursor.fetchall()
            
            # Convert Row objects to dictionaries for easier template handling
            events = [dict(event) for event in events]
        except Error as e:
            print(f"Error fetching events: {e}")
        finally:
            conn.close()
    
    return render_template('events.html', events=events)

@app.route('/artifacts')
def artifacts():
    return render_template('artifacts.html')

@app.route('/about')
def about():
    return render_template('about.html')

# @app.route('/profile', methods=['GET', 'POST'])
# def profile():
#     if 'admin_email' not in session:  # Check for admin session
#         return redirect(url_for('adminLogin'))
    
#     conn = create_connection()
#     admin = None
#     error = None
#     success = None
    
#     try:
#         if conn is not None:
#             cursor = conn.cursor()
#             # Query the 'admins' table (not 'users')
#             cursor.execute('SELECT * FROM admins WHERE email = ?', (session['admin_email'],))
#             admin_data = cursor.fetchone()
            
#             if admin_data:
#                 columns = ['id', 'first_name', 'last_name', 'email', 'password']
#                 admin = dict(zip(columns, admin_data))
                
#                 if request.method == 'POST':
#                     # Update only admin-specific fields (no address/phone)
#                     cursor.execute('''
#                         UPDATE admins SET 
#                         first_name = ?,
#                         last_name = ?
#                         WHERE email = ?
#                     ''', (
#                         request.form.get('first_name'),
#                         request.form.get('last_name'),
#                         session['admin_email']
#                     ))
#                     conn.commit()
#                     success = "Profile updated successfully!"
                    
#     except Error as e:
#         print(f"Database error: {e}")
#         error = "An error occurred while processing your request"
#     finally:
#         if conn:
#             conn.close()
    
#     if not admin:
#         error = "Admin not found"
#         return redirect(url_for('adminLogin'))  # Redirect to admin login
    
#     return render_template(
#         'profile.html', 
#         user=admin,  # Pass admin data to template (renamed for consistency)
#         csrf_token=generate_csrf(),
#         error=error,
#         success=success
#     )

# Run the application
if __name__ == '__main__':
    app.run(debug=True)