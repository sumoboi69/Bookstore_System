import os
from flask import Flask, render_template

# 1. Get the absolute path to the folder containing this script
base_dir = os.path.abspath(os.path.dirname(__file__))

# 2. Define the exact paths for templates and static files
template_path = os.path.join(base_dir, 'templates')
static_path = os.path.join(base_dir, 'static')

# 3. Initialize Flask with these explicit paths
app = Flask(__name__, template_folder=template_path, static_folder=static_path)
app.secret_key = 'dev_key'

# --- DUMMY DATA FOR TESTING ---
# This simulates data coming from a database so you can check the design
sample_books = [
    {"isbn": "978-1", "title": "Database System Concepts", "author": "A. Silberschatz", "year": 2025, "price": 120.00, "category": "Science", "stock_quantity": 50, "threshold": 5, "publisher": "McGraw-Hill"},
    {"isbn": "978-2", "title": "History of Modern Art", "author": "H. H. Arnason", "year": 2024, "price": 85.50, "category": "Art", "stock_quantity": 3, "threshold": 10, "publisher": "Pearson"},
    {"isbn": "978-3", "title": "World Geography", "author": "R. Boehm", "year": 2023, "price": 50.00, "category": "Geography", "stock_quantity": 0, "threshold": 5, "publisher": "Glencoe"},
    {"isbn": "978-4", "title": "Clean Code", "author": "Robert C. Martin", "year": 2008, "price": 45.00, "category": "Science", "stock_quantity": 100, "threshold": 10, "publisher": "Prentice Hall"},
]

sample_cart = [
    {"isbn": "978-1", "title": "Database System Concepts", "price": 120.00, "quantity": 1},
    {"isbn": "978-2", "title": "History of Modern Art", "price": 85.50, "quantity": 2},
]

sample_orders = [
    {"id": 101, "date": "2025-12-01", "total_price": 205.50, "items": [{"isbn": "978-1", "title": "Database Systems", "quantity": 1, "price": 120.00}]}
]

# --- VIEW ROUTES ---

@app.route('/')
def index():
    return render_template('index.html', books=sample_books)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/cart')
def cart():
    # Calculates a fake total for the UI
    total = sum(item['price'] * item['quantity'] for item in sample_cart)
    return render_template('customer_templates/cart.html', cart_items=sample_cart, total_price=total)

@app.route('/checkout')
def checkout():
    # Pass a fake user object to avoid errors in the checkout template
    fake_user = {"fullname": "Mohamed Kasem", "address": "123 Alexandria St", "phone": "+20 100 200 3000"}
    return render_template('customer_templates/checkout.html', cart_items=sample_cart, total_price=291.00, current_user=fake_user)

@app.route('/profile')
def profile():
    return render_template('customer_templates/profile.html')

@app.route('/my_orders')
def my_orders():
    return render_template('customer_templates/my_orders.html', orders=sample_orders)

@app.route('/book/<isbn>')
def book_details(isbn):
    # Find the book in our dummy list
    book = next((b for b in sample_books if b['isbn'] == isbn), sample_books[0])
    return render_template('book_details.html', book=book)

# --- ADMIN VIEW ROUTES ---

@app.route('/admin_dashboard')
def admin_dashboard():
    return render_template('admin_templates/admin_dashboard.html')

@app.route('/manage_books')
def manage_books():
    return render_template('admin_templates/manage_books.html', books=sample_books)

@app.route('/reports')
def reports():
    return render_template('admin_templates/reports.html')

@app.route('/confirm_orders')
def confirm_orders():
    return render_template('admin_templates/confirm_orders.html')

if __name__ == '__main__':
    print("Frontend Viewer running! Go to http://127.0.0.1:5000")
    app.run(debug=True, port=5000)