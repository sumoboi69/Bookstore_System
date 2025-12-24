"""
Authentication routes: Login, Signup, Logout
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from database import execute_query, get_db_cursor

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and handler"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Fetch user from database
        user = User.get_by_username(username)

        if user and check_password_hash(user.password, password):
            login_user(user, remember=request.form.get('remember'))

            # Redirect based on account type
            if user.is_admin:
                return redirect(url_for('admin.admin_dashboard'))
            else:
                return redirect(url_for('customer.index'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')


@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    """Customer signup page and handler"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        first_name = request.form.get('fname')
        last_name = request.form.get('lname')
        email = request.form.get('email')
        phone = request.form.get('phone')
        address = request.form.get('address')

        # Check if username already exists
        query_check = """
            SELECT Username FROM USER_ACCOUNT WHERE Username = %s
        """
        existing_user = execute_query(query_check, (username,), fetch_one=True)

        if existing_user:
            flash('Username already exists. Please choose another.', 'danger')
            return render_template('signup.html')

        # Check if email already exists
        query_email = """
            SELECT Email_Address FROM USER_ACCOUNT WHERE Email_Address = %s
        """
        existing_email = execute_query(query_email, (email,), fetch_one=True)

        if existing_email:
            flash('Email already registered.', 'danger')
            return render_template('signup.html')

        # Hash password
        hashed_password = generate_password_hash(password)

        try:
            # Create user account
            with get_db_cursor(commit=True) as cursor:
                # Insert into USER_ACCOUNT
                query_user = """
                    INSERT INTO USER_ACCOUNT (Username, Password, First_Name, Last_Name, Email_Address, Phone_Number, Shipping_Address, Account_Type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, 'Customer')
                """
                cursor.execute(query_user, (username, hashed_password, first_name, last_name, email, phone, address))

                # Insert into CUSTOMER table
                query_customer = """
                    INSERT INTO CUSTOMER (Username) VALUES (%s)
                """
                cursor.execute(query_customer, (username,))

                # Create shopping cart for the new customer
                query_cart = """
                    INSERT INTO SHOPPING_CART (Customer_Username) VALUES (%s)
                """
                cursor.execute(query_cart, (username,))

            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            flash(f'Error creating account: {str(e)}', 'danger')
            return render_template('signup.html')

    return render_template('signup.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Logout handler"""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('customer.index'))

