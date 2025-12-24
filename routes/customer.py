"""
Customer routes: Home, Search, Book Details, Cart, Checkout, Orders, Profile
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from database import execute_query, get_db_cursor
from datetime import datetime

customer_bp = Blueprint('customer', __name__)


@customer_bp.route('/')
def index():
    """Home page with featured books"""
    # Get latest 4 books as new arrivals
    query = """
        SELECT b.*, p.Name as Publisher_Name,
               GROUP_CONCAT(CONCAT(a.First_Name, ' ', a.Last_Name) SEPARATOR ', ') as Authors
        FROM BOOK b
        JOIN PUBLISHER p ON b.Publisher_ID = p.Publisher_ID
        LEFT JOIN BOOK_AUTHOR ba ON b.ISBN = ba.ISBN
        LEFT JOIN AUTHOR a ON ba.Author_ID = a.Author_ID
        WHERE b.Stock_Quantity > 0
        GROUP BY b.ISBN
        ORDER BY b.ISBN DESC
        LIMIT 4
    """
    new_arrivals = execute_query(query) or []

    return render_template('index.html', new_arrivals=new_arrivals)


@customer_bp.route('/search')
def search():
    """Search for books"""
    search_query = request.args.get('q', '')
    search_type = request.args.get('search_type', 'title')
    category = request.args.get('category', '')

    books = []

    if category:
        # Search by category
        query = """
            SELECT b.*, p.Name as Publisher_Name, 
                   GROUP_CONCAT(CONCAT(a.First_Name, ' ', a.Last_Name) SEPARATOR ', ') as Authors
            FROM BOOK b
            JOIN PUBLISHER p ON b.Publisher_ID = p.Publisher_ID
            LEFT JOIN BOOK_AUTHOR ba ON b.ISBN = ba.ISBN
            LEFT JOIN AUTHOR a ON ba.Author_ID = a.Author_ID
            WHERE b.Category = %s
            GROUP BY b.ISBN
        """
        books = execute_query(query, (category,))

    elif search_query:
        # Search based on type
        if search_type == 'title':
            query = """
                SELECT b.*, p.Name as Publisher_Name,
                       GROUP_CONCAT(CONCAT(a.First_Name, ' ', a.Last_Name) SEPARATOR ', ') as Authors
                FROM BOOK b
                JOIN PUBLISHER p ON b.Publisher_ID = p.Publisher_ID
                LEFT JOIN BOOK_AUTHOR ba ON b.ISBN = ba.ISBN
                LEFT JOIN AUTHOR a ON ba.Author_ID = a.Author_ID
                WHERE b.Title LIKE %s
                GROUP BY b.ISBN
            """
            books = execute_query(query, (f'%{search_query}%',))

        elif search_type == 'isbn':
            query = """
                SELECT b.*, p.Name as Publisher_Name,
                       GROUP_CONCAT(CONCAT(a.First_Name, ' ', a.Last_Name) SEPARATOR ', ') as Authors
                FROM BOOK b
                JOIN PUBLISHER p ON b.Publisher_ID = p.Publisher_ID
                LEFT JOIN BOOK_AUTHOR ba ON b.ISBN = ba.ISBN
                LEFT JOIN AUTHOR a ON ba.Author_ID = a.Author_ID
                WHERE b.ISBN = %s
                GROUP BY b.ISBN
            """
            books = execute_query(query, (search_query,))

        elif search_type == 'author':
            query = """
                SELECT b.*, p.Name as Publisher_Name,
                       GROUP_CONCAT(CONCAT(a.First_Name, ' ', a.Last_Name) SEPARATOR ', ') as Authors
                FROM BOOK b
                JOIN PUBLISHER p ON b.Publisher_ID = p.Publisher_ID
                JOIN BOOK_AUTHOR ba ON b.ISBN = ba.ISBN
                JOIN AUTHOR a ON ba.Author_ID = a.Author_ID
                WHERE CONCAT(a.First_Name, ' ', a.Last_Name) LIKE %s
                GROUP BY b.ISBN
            """
            books = execute_query(query, (f'%{search_query}%',))

        elif search_type == 'publisher':
            query = """
                SELECT b.*, p.Name as Publisher_Name,
                       GROUP_CONCAT(CONCAT(a.First_Name, ' ', a.Last_Name) SEPARATOR ', ') as Authors
                FROM BOOK b
                JOIN PUBLISHER p ON b.Publisher_ID = p.Publisher_ID
                LEFT JOIN BOOK_AUTHOR ba ON b.ISBN = ba.ISBN
                LEFT JOIN AUTHOR a ON ba.Author_ID = a.Author_ID
                WHERE p.Name LIKE %s
                GROUP BY b.ISBN
            """
            books = execute_query(query, (f'%{search_query}%',))
    else:
        # No search query - show all books
        query = """
            SELECT b.*, p.Name as Publisher_Name,
                   GROUP_CONCAT(CONCAT(a.First_Name, ' ', a.Last_Name) SEPARATOR ', ') as Authors
            FROM BOOK b
            JOIN PUBLISHER p ON b.Publisher_ID = p.Publisher_ID
            LEFT JOIN BOOK_AUTHOR ba ON b.ISBN = ba.ISBN
            LEFT JOIN AUTHOR a ON ba.Author_ID = a.Author_ID
            GROUP BY b.ISBN
            ORDER BY b.Title
        """
        books = execute_query(query)

    return render_template('search_results.html', books=books, query=search_query)


@customer_bp.route('/book/<isbn>')
def book_details(isbn):
    """Display book details"""
    query = """
        SELECT b.*, p.Name as Publisher_Name,
               GROUP_CONCAT(CONCAT(a.First_Name, ' ', a.Last_Name) SEPARATOR ', ') as Authors
        FROM BOOK b
        JOIN PUBLISHER p ON b.Publisher_ID = p.Publisher_ID
        LEFT JOIN BOOK_AUTHOR ba ON b.ISBN = ba.ISBN
        LEFT JOIN AUTHOR a ON ba.Author_ID = a.Author_ID
        WHERE b.ISBN = %s
        GROUP BY b.ISBN
    """
    book = execute_query(query, (isbn,), fetch_one=True)

    if not book:
        flash('Book not found', 'danger')
        return redirect(url_for('customer.index'))

    return render_template('book_details.html', book=book)


@customer_bp.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    """Add book to shopping cart"""
    isbn = request.form.get('isbn')
    quantity = int(request.form.get('quantity', 1))

    try:
        with get_db_cursor(commit=True) as cursor:
            # Get customer's cart ID
            query_cart = """
                SELECT Cart_ID FROM SHOPPING_CART WHERE Customer_Username = %s
            """
            cursor.execute(query_cart, (current_user.username,))
            cart = cursor.fetchone()

            if not cart:
                # Create cart if doesn't exist
                query_create_cart = """
                    INSERT INTO SHOPPING_CART (Customer_Username) VALUES (%s)
                """
                cursor.execute(query_create_cart, (current_user.username,))
                cart_id = cursor.lastrowid
            else:
                cart_id = cart['Cart_ID']

            # Check if item already in cart
            query_check = """
                SELECT Quantity FROM CART_ITEM WHERE Cart_ID = %s AND ISBN = %s
            """
            cursor.execute(query_check, (cart_id, isbn))
            existing_item = cursor.fetchone()

            if existing_item:
                # Update quantity
                query_update = """
                    UPDATE CART_ITEM SET Quantity = Quantity + %s WHERE Cart_ID = %s AND ISBN = %s
                """
                cursor.execute(query_update, (quantity, cart_id, isbn))
            else:
                # Insert new item
                query_insert = """
                    INSERT INTO CART_ITEM (Cart_ID, ISBN, Quantity) VALUES (%s, %s, %s)
                """
                cursor.execute(query_insert, (cart_id, isbn, quantity))

        flash('Book added to cart!', 'success')
    except Exception as e:
        flash(f'Error adding to cart: {str(e)}', 'danger')

    return redirect(request.referrer or url_for('customer.index'))


@customer_bp.route('/cart')
@login_required
def cart():
    """View shopping cart"""
    query = """
        SELECT ci.*, b.Title, b.Selling_Price, b.Stock_Quantity
        FROM CART_ITEM ci
        JOIN SHOPPING_CART sc ON ci.Cart_ID = sc.Cart_ID
        JOIN BOOK b ON ci.ISBN = b.ISBN
        WHERE sc.Customer_Username = %s
    """
    cart_items = execute_query(query, (current_user.username,))

    total_price = sum(item['Selling_Price'] * item['Quantity'] for item in cart_items) if cart_items else 0

    return render_template('customer_templates/cart.html', cart_items=cart_items, total_price=total_price)


@customer_bp.route('/update_cart_quantity', methods=['POST'])
@login_required
def update_cart_quantity():
    """Update quantity of an item in cart"""
    isbn = request.form.get('isbn')
    action = request.form.get('action')  # 'increase' or 'decrease'

    try:
        with get_db_cursor(commit=True) as cursor:
            # Get current quantity
            query_get = """
                SELECT ci.Quantity, b.Stock_Quantity
                FROM CART_ITEM ci
                JOIN SHOPPING_CART sc ON ci.Cart_ID = sc.Cart_ID
                JOIN BOOK b ON ci.ISBN = b.ISBN
                WHERE sc.Customer_Username = %s AND ci.ISBN = %s
            """
            cursor.execute(query_get, (current_user.username, isbn))
            result = cursor.fetchone()

            if result:
                current_qty = result['Quantity']
                stock_qty = result['Stock_Quantity']

                if action == 'increase':
                    new_qty = current_qty + 1
                    if new_qty > stock_qty:
                        flash('Cannot add more items than available in stock', 'warning')
                        return redirect(url_for('customer.cart'))
                elif action == 'decrease':
                    new_qty = current_qty - 1
                    if new_qty < 1:
                        # If quantity would be 0, remove item instead
                        query_delete = """
                            DELETE ci FROM CART_ITEM ci
                            JOIN SHOPPING_CART sc ON ci.Cart_ID = sc.Cart_ID
                            WHERE sc.Customer_Username = %s AND ci.ISBN = %s
                        """
                        cursor.execute(query_delete, (current_user.username, isbn))
                        flash('Item removed from cart', 'info')
                        return redirect(url_for('customer.cart'))
                else:
                    return redirect(url_for('customer.cart'))

                # Update quantity
                query_update = """
                    UPDATE CART_ITEM ci
                    JOIN SHOPPING_CART sc ON ci.Cart_ID = sc.Cart_ID
                    SET ci.Quantity = %s
                    WHERE sc.Customer_Username = %s AND ci.ISBN = %s
                """
                cursor.execute(query_update, (new_qty, current_user.username, isbn))

    except Exception as e:
        flash(f'Error updating cart: {str(e)}', 'danger')

    return redirect(url_for('customer.cart'))


@customer_bp.route('/remove_from_cart', methods=['POST'])
@login_required
def remove_from_cart():
    """Remove item from cart"""
    isbn = request.form.get('isbn')

    query = """
        DELETE ci FROM CART_ITEM ci
        JOIN SHOPPING_CART sc ON ci.Cart_ID = sc.Cart_ID
        WHERE sc.Customer_Username = %s AND ci.ISBN = %s
    """
    execute_query(query, (current_user.username, isbn), commit=True)

    flash('Item removed from cart', 'info')
    return redirect(url_for('customer.cart'))


@customer_bp.route('/checkout')
@login_required
def checkout():
    """Checkout page"""
    query = """
        SELECT ci.*, b.Title, b.Selling_Price
        FROM CART_ITEM ci
        JOIN SHOPPING_CART sc ON ci.Cart_ID = sc.Cart_ID
        JOIN BOOK b ON ci.ISBN = b.ISBN
        WHERE sc.Customer_Username = %s
    """
    cart_items = execute_query(query, (current_user.username,))

    if not cart_items:
        flash('Your cart is empty', 'warning')
        return redirect(url_for('customer.cart'))

    total_price = sum(item['Selling_Price'] * item['Quantity'] for item in cart_items)
    cart_count = len(cart_items)

    return render_template('customer_templates/checkout.html',
                         cart_items=cart_items,
                         total_price=total_price,
                         cart_count=cart_count)


@customer_bp.route('/process_checkout', methods=['POST'])
@login_required
def process_checkout():
    """Process checkout and create sales transaction"""
    cc_number = request.form.get('cc_number', '').replace(' ', '')  # Remove spaces
    cc_expiration = request.form.get('cc_expiration')

    try:
        with get_db_cursor(commit=True) as cursor:
            # Get cart items
            query_cart = """
                SELECT ci.*, b.Selling_Price, b.Stock_Quantity
                FROM CART_ITEM ci
                JOIN SHOPPING_CART sc ON ci.Cart_ID = sc.Cart_ID
                JOIN BOOK b ON ci.ISBN = b.ISBN
                WHERE sc.Customer_Username = %s
            """
            cursor.execute(query_cart, (current_user.username,))
            cart_items = cursor.fetchall()

            if not cart_items:
                flash('Cart is empty', 'warning')
                return redirect(url_for('customer.cart'))

            # Calculate total
            total_amount = sum(item['Selling_Price'] * item['Quantity'] for item in cart_items)

            # Check stock availability
            for item in cart_items:
                if item['Stock_Quantity'] < item['Quantity']:
                    flash(f'Insufficient stock for {item["ISBN"]}', 'danger')
                    return redirect(url_for('customer.cart'))

            # Create sales transaction
            query_transaction = """
                INSERT INTO SALES_TRANSACTION (Customer_Username, Transaction_Date, Total_Amount, Credit_Card_Number, Expiry_Date)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query_transaction,
                         (current_user.username, datetime.now(), total_amount, cc_number, cc_expiration))
            transaction_id = cursor.lastrowid

            # Insert sale items and update stock
            for item in cart_items:
                # Insert sale item
                query_sale_item = """
                    INSERT INTO SALE_ITEM (Transaction_ID, ISBN, Quantity_Sold, Price_At_Sale)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query_sale_item,
                             (transaction_id, item['ISBN'], item['Quantity'], item['Selling_Price']))

                # Update book stock
                query_update_stock = """
                    UPDATE BOOK SET Stock_Quantity = Stock_Quantity - %s WHERE ISBN = %s
                """
                cursor.execute(query_update_stock, (item['Quantity'], item['ISBN']))

            # Clear cart
            query_clear_cart = """
                DELETE ci FROM CART_ITEM ci
                JOIN SHOPPING_CART sc ON ci.Cart_ID = sc.Cart_ID
                WHERE sc.Customer_Username = %s
            """
            cursor.execute(query_clear_cart, (current_user.username,))

        flash('Order placed successfully!', 'success')
        return redirect(url_for('customer.my_orders'))

    except Exception as e:
        flash(f'Error processing order: {str(e)}', 'danger')
        return redirect(url_for('customer.checkout'))


@customer_bp.route('/my_orders')
@login_required
def my_orders():
    """View order history"""
    query = """
        SELECT st.Transaction_ID, st.Transaction_Date, st.Total_Amount,
               si.ISBN, si.Quantity_Sold, si.Price_At_Sale,
               b.Title
        FROM SALES_TRANSACTION st
        LEFT JOIN SALE_ITEM si ON st.Transaction_ID = si.Transaction_ID
        LEFT JOIN BOOK b ON si.ISBN = b.ISBN
        WHERE st.Customer_Username = %s
        ORDER BY st.Transaction_Date DESC
    """
    results = execute_query(query, (current_user.username,))

    # Group items by transaction
    orders_dict = {}
    if results:
        for row in results:
            trans_id = row['Transaction_ID']
            if trans_id not in orders_dict:
                orders_dict[trans_id] = {
                    'id': trans_id,
                    'date': row['Transaction_Date'].strftime('%Y-%m-%d %H:%M') if row['Transaction_Date'] else 'N/A',
                    'total_price': float(row['Total_Amount']) if row['Total_Amount'] else 0,
                    'order_items': []  # Changed from 'items' to 'order_items' to avoid conflict with dict.items()
                }

            # Add item if it exists
            if row['ISBN']:
                orders_dict[trans_id]['order_items'].append({
                    'isbn': row['ISBN'],
                    'title': row['Title'] or 'Unknown',
                    'quantity': row['Quantity_Sold'],
                    'price': float(row['Price_At_Sale']) if row['Price_At_Sale'] else 0
                })

    # Convert dict to list
    orders = list(orders_dict.values())

    return render_template('customer_templates/my_orders.html', orders=orders)


@customer_bp.route('/profile')
@login_required
def profile():
    """View and edit profile"""
    return render_template('customer_templates/profile.html')


@customer_bp.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    first_name = request.form.get('fname')
    last_name = request.form.get('lname')
    email = request.form.get('email')
    phone = request.form.get('phone')
    address = request.form.get('address')
    new_password = request.form.get('password')

    try:
        with get_db_cursor(commit=True) as cursor:
            if new_password:
                # Update with new password
                from werkzeug.security import generate_password_hash
                hashed_password = generate_password_hash(new_password)

                query = """
                    UPDATE USER_ACCOUNT 
                    SET First_Name = %s, Last_Name = %s, Email_Address = %s, 
                        Phone_Number = %s, Shipping_Address = %s, Password = %s
                    WHERE Username = %s
                """
                cursor.execute(query, (first_name, last_name, email, phone, address, hashed_password, current_user.username))
            else:
                # Update without password
                query = """
                    UPDATE USER_ACCOUNT 
                    SET First_Name = %s, Last_Name = %s, Email_Address = %s, 
                        Phone_Number = %s, Shipping_Address = %s
                    WHERE Username = %s
                """
                cursor.execute(query, (first_name, last_name, email, phone, address, current_user.username))

        flash('Profile updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating profile: {str(e)}', 'danger')

    return redirect(url_for('customer.profile'))

