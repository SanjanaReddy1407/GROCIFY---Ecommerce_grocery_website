from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import os
import json
from datetime import datetime

# --- Configuration and Setup ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "gro_orders.db") 

app = Flask(__name__)
# A secret key is required for using flash messages
app.secret_key = 'your_grocify_secret_key_change_me' 


# --- Database Helper Functions ---
def get_db_connection():
    """Establishes and returns a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

def init_db():
    """Initializes the database and creates the 'fb' (feedback) and 'orders' tables."""
    conn = None 
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # 1. Feedback Table (From your original code)
        c.execute("""
            CREATE TABLE IF NOT EXISTS fb (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                course TEXT,
                rating INTEGER,
                comments TEXT
            );
        """)
        
        # 2. Orders Table (New for placeorder.html integration)
        c.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                customer_email TEXT NOT NULL,
                shipping_address TEXT NOT NULL,
                phone_number TEXT,
                order_details_json TEXT NOT NULL,
                total_value REAL NOT NULL,
                order_date TEXT NOT NULL
            );
        """)
        
        conn.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        if conn:
            conn.close()

# --- Routes ---

# Handles both displaying the order form (GET) and submitting the order (POST)
@app.route('/', methods=['GET', 'POST'])
def index():
    # Handle the POST request from placeorder.html (Order Submission)
    if request.method == 'POST':
        # 1. Get shipping details
        name = request.form.get('name')
        email = request.form.get('email')
        address = request.form.get('address')
        phone = request.form.get('phone')
        
        # 2. Get order details (hidden fields from placeorder.html)
        order_details_json = request.form.get('order_details_json')
        order_total_value = request.form.get('order_total_value')

        if not all([name, email, address, order_details_json, order_total_value]):
            flash('Error: Missing required form data. Please check your cart and details.', 'error')
            return redirect(url_for('index'))

        conn = None 
        try:
            conn = get_db_connection()
            c = conn.cursor()

            # Insert the new order into the 'orders' table (Secure parameter substitution used)
            query = """
            INSERT INTO orders 
            (customer_name, customer_email, shipping_address, phone_number, order_details_json, total_value, order_date) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            # Note: order_total_value is converted to float before insertion
            c.execute(query, (
                name, 
                email, 
                address, 
                phone, 
                order_details_json, 
                float(order_total_value),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            
            conn.commit()
            
            # Success message for the user
            flash(f'Order Confirmed! Thank you, {name}. Your total is Rs. {float(order_total_value):.2f}.', 'success')
            
            # Use POST-Redirect-GET pattern to prevent form resubmission
            return redirect(url_for('index')) 

        except (sqlite3.Error, ValueError) as e:
            print(f"Error during order submission: {e}")
            flash('A server error occurred while placing your order. Please try again.', 'error')
            return redirect(url_for('index'))
        finally:
            if conn:
                conn.close()

    # Handle the GET request (render the page)
    # Renders the placeorder.html file. Flash messages are handled by the template.
    return render_template('placeorder.html')


# --- Feedback Routes (Fixed and Kept) ---

@app.route('/submit', methods=['POST'])
def submit():
    """Handles the feedback form submission (Assuming a separate feedback form)."""
    name = request.form.get('name')
    course = request.form.get('course')
    rating = request.form.get('rating')
    comments = request.form.get('comments')

    conn = None 
    try:
        conn = get_db_connection()
        c = conn.cursor()
        # Using secure parameter substitution
        query = "INSERT INTO fb (name, course, rating, comments) VALUES (?, ?, ?, ?)"
        c.execute(query, (name, course, rating, comments))
        conn.commit()
        return render_template('thanks.html', name=name)
    except sqlite3.Error as e:
        print(f"Database error during submission: {e}")
        return "An error occurred while submitting feedback.", 500
    finally:
        if conn:
            conn.close()

@app.route('/view')
def view():
    """Retrieves and displays all entries from the 'fb' table."""
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM fb") 
        rows = c.fetchall()
        feedback_list = [dict(row) for row in rows]
        return str(feedback_list)
    except sqlite3.Error as e:
        print(f"Database error during view: {e}")
        return "An error occurred while viewing feedback.", 500
    finally:
        if conn:
            conn.close()

# --- Application Startup ---
if __name__ == '__main__':
    # Initialize the database and tables before starting the server
    init_db() 
    app.run(debug=True)

    