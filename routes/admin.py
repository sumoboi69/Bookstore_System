"""
Admin routes: Dashboard, Manage Books, Confirm Orders, Reports
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from database import execute_query, get_db_cursor
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Access denied. Admin privileges required.', 'danger')
            return redirect(url_for('customer.index'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """Admin dashboard with statistics"""
    # Get monthly sales
    query_sales = """
        SELECT COALESCE(SUM(Total_Amount), 0) as monthly_sales
        FROM SALES_TRANSACTION
        WHERE MONTH(Transaction_Date) = MONTH(CURRENT_DATE())
          AND YEAR(Transaction_Date) = YEAR(CURRENT_DATE())
    """
    sales_data = execute_query(query_sales, fetch_one=True)
    monthly_sales = sales_data['monthly_sales'] if sales_data else 0

    # Get pending orders count
    query_pending = """
        SELECT COUNT(*) as pending_count
        FROM PUBLISHER_ORDER
        WHERE Order_Status = 'Pending'
    """
    pending_data = execute_query(query_pending, fetch_one=True)
    pending_orders = pending_data['pending_count'] if pending_data else 0

    # Get low stock items count
    query_low_stock = """
        SELECT COUNT(*) as low_stock_count
        FROM BOOK
        WHERE Stock_Quantity <= Stock_Threshold
    """
    low_stock_data = execute_query(query_low_stock, fetch_one=True)
    low_stock_count = low_stock_data['low_stock_count'] if low_stock_data else 0

    return render_template('admin_templates/admin_dashboard.html',
                         monthly_sales=monthly_sales,
                         pending_orders=pending_orders,
                         low_stock_count=low_stock_count)


@admin_bp.route('/manage_books')
@login_required
@admin_required
def manage_books():
    """Manage books inventory"""
    search_query = request.args.get('q', '')
    search_type = request.args.get('search_type', 'isbn')

    if search_query:
        if search_type == 'isbn':
            query = """
                SELECT b.*, p.Name as publisher
                FROM BOOK b
                JOIN PUBLISHER p ON b.Publisher_ID = p.Publisher_ID
                WHERE b.ISBN = %s
            """
            books = execute_query(query, (search_query,))
        else:  # title
            query = """
                SELECT b.*, p.Name as publisher
                FROM BOOK b
                JOIN PUBLISHER p ON b.Publisher_ID = p.Publisher_ID
                WHERE b.Title LIKE %s
            """
            books = execute_query(query, (f'%{search_query}%',))
    else:
        # Get all books
        query = """
            SELECT b.*, p.Name as publisher
            FROM BOOK b
            JOIN PUBLISHER p ON b.Publisher_ID = p.Publisher_ID
            ORDER BY b.Title
        """
        books = execute_query(query)

    # Get all authors and publishers for the add book form dropdowns
    authors = execute_query("SELECT * FROM AUTHOR ORDER BY Last_Name, First_Name")
    publishers = execute_query("SELECT * FROM PUBLISHER ORDER BY Name")

    # Format books for template
    if books:
        for book in books:
            book['isbn'] = book['ISBN']
            book['title'] = book['Title']
            book['category'] = book['Category']
            book['stock_quantity'] = book['Stock_Quantity']
            book['threshold'] = book['Stock_Threshold']
            book['price'] = book['Selling_Price']

    return render_template('admin_templates/manage_books.html',
                         books=books or [],
                         authors=authors or [],
                         publishers=publishers or [])


@admin_bp.route('/add_book', methods=['POST'])
@login_required
@admin_required
def add_book():
    """Add a new book to inventory"""
    isbn = request.form.get('isbn')
    title = request.form.get('title')
    category = request.form.get('category')
    year = request.form.get('year')
    publisher_id = request.form.get('publisher_id')
    price = request.form.get('price')
    stock = request.form.get('stock')
    threshold = request.form.get('threshold')
    author_ids = request.form.getlist('author_ids')  # Get multiple author IDs

    # Validate that at least one author is selected
    if not author_ids:
        flash('Error: At least one author must be selected', 'danger')
        return redirect(url_for('admin.manage_books'))

    try:
        with get_db_cursor(commit=True) as cursor:
            # Insert book
            query_book = """
                INSERT INTO BOOK (ISBN, Title, Publication_Year, Selling_Price, Category, 
                                  Publisher_ID, Stock_Quantity, Stock_Threshold)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query_book, (isbn, title, year, price, category, publisher_id, stock, threshold))

            # Insert book-author relationships
            query_author = "INSERT INTO BOOK_AUTHOR (ISBN, Author_ID) VALUES (%s, %s)"
            for author_id in author_ids:
                cursor.execute(query_author, (isbn, author_id))

        flash('Book and author(s) added successfully!', 'success')
    except Exception as e:
        flash(f'Error adding book: {str(e)}', 'danger')

    return redirect(url_for('admin.manage_books'))


@admin_bp.route('/update_book', methods=['POST'])
@login_required
@admin_required
def update_book():
    """Update book stock and price"""
    isbn = request.form.get('isbn')
    stock = request.form.get('stock')
    price = request.form.get('price')

    try:
        query = """
            UPDATE BOOK 
            SET Stock_Quantity = %s, Selling_Price = %s
            WHERE ISBN = %s
        """
        execute_query(query, (stock, price, isbn), commit=True)

        flash('Book updated successfully!', 'success')
    except Exception as e:
        flash(f'Error updating book: {str(e)}', 'danger')

    return redirect(url_for('admin.manage_books'))


@admin_bp.route('/confirm_orders')
@login_required
@admin_required
def confirm_orders():
    """View and confirm publisher orders"""
    status_filter = request.args.get('status', 'pending')

    if status_filter == 'pending':
        query = """
            SELECT po.Order_ID, po.Order_Date, po.Publisher_ID, po.Order_Status,
                   p.Name as Publisher_Name,
                   oi.ISBN, oi.Quantity_Ordered,
                   b.Title as Book_Title
            FROM PUBLISHER_ORDER po
            JOIN PUBLISHER p ON po.Publisher_ID = p.Publisher_ID
            JOIN ORDER_ITEM oi ON po.Order_ID = oi.Order_ID
            JOIN BOOK b ON oi.ISBN = b.ISBN
            WHERE po.Order_Status = 'Pending'
            ORDER BY po.Order_Date DESC
        """
        orders = execute_query(query)
    elif status_filter == 'confirmed':
        query = """
            SELECT po.Order_ID, po.Order_Date, po.Publisher_ID, po.Order_Status,
                   p.Name as Publisher_Name,
                   oi.ISBN, oi.Quantity_Ordered,
                   b.Title as Book_Title
            FROM PUBLISHER_ORDER po
            JOIN PUBLISHER p ON po.Publisher_ID = p.Publisher_ID
            JOIN ORDER_ITEM oi ON po.Order_ID = oi.Order_ID
            JOIN BOOK b ON oi.ISBN = b.ISBN
            WHERE po.Order_Status = 'Confirmed'
            ORDER BY po.Order_Date DESC
        """
        orders = execute_query(query)
    else:  # all
        query = """
            SELECT po.Order_ID, po.Order_Date, po.Publisher_ID, po.Order_Status,
                   p.Name as Publisher_Name,
                   oi.ISBN, oi.Quantity_Ordered,
                   b.Title as Book_Title
            FROM PUBLISHER_ORDER po
            JOIN PUBLISHER p ON po.Publisher_ID = p.Publisher_ID
            JOIN ORDER_ITEM oi ON po.Order_ID = oi.Order_ID
            JOIN BOOK b ON oi.ISBN = b.ISBN
            ORDER BY po.Order_Date DESC
        """
        orders = execute_query(query)

    return render_template('admin_templates/confirm_orders.html', orders=orders or [], status_filter=status_filter)


@admin_bp.route('/confirm_order/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def confirm_order(order_id):
    """Confirm a publisher order (triggers stock update)"""
    try:
        query = """
            UPDATE PUBLISHER_ORDER 
            SET Order_Status = 'Confirmed'
            WHERE Order_ID = %s
        """
        execute_query(query, (order_id,), commit=True)

        flash('Order confirmed! Stock has been updated.', 'success')
    except Exception as e:
        flash(f'Error confirming order: {str(e)}', 'danger')

    return redirect(url_for('admin.confirm_orders'))


@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """View various reports"""
    # Get last month sales
    query_last_month = """
        SELECT COALESCE(SUM(Total_Amount), 0) as total_sales
        FROM SALES_TRANSACTION
        WHERE Transaction_Date >= DATE_SUB(CURRENT_DATE(), INTERVAL 1 MONTH)
    """
    last_month_data = execute_query(query_last_month, fetch_one=True)
    last_month_sales = last_month_data['total_sales'] if last_month_data else 0

    # Get top 5 customers (last 3 months)
    query_top_customers = """
        SELECT u.First_Name, u.Last_Name, 
               SUM(st.Total_Amount) as total_spent
        FROM SALES_TRANSACTION st
        JOIN USER_ACCOUNT u ON st.Customer_Username = u.Username
        WHERE st.Transaction_Date >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH)
        GROUP BY st.Customer_Username
        ORDER BY total_spent DESC
        LIMIT 5
    """
    top_customers = execute_query(query_top_customers)

    # Format customer data
    if top_customers:
        for idx, customer in enumerate(top_customers, 1):
            customer['rank'] = idx
            customer['name'] = f"{customer['First_Name']} {customer['Last_Name']}"

    # Get top selling books (last 3 months)
    query_top_books = """
        SELECT b.Title, SUM(si.Quantity_Sold) as copies_sold
        FROM SALE_ITEM si
        JOIN SALES_TRANSACTION st ON si.Transaction_ID = st.Transaction_ID
        JOIN BOOK b ON si.ISBN = b.ISBN
        WHERE st.Transaction_Date >= DATE_SUB(CURRENT_DATE(), INTERVAL 3 MONTH)
        GROUP BY si.ISBN
        ORDER BY copies_sold DESC
        LIMIT 10
    """
    top_books = execute_query(query_top_books)

    # Get replenishment history
    query_replenishment = """
        SELECT b.ISBN, b.Title, 
               COUNT(po.Order_ID) as times_ordered,
               MAX(po.Order_Date) as last_order_date
        FROM BOOK b
        LEFT JOIN ORDER_ITEM oi ON b.ISBN = oi.ISBN
        LEFT JOIN PUBLISHER_ORDER po ON oi.Order_ID = po.Order_ID
        GROUP BY b.ISBN
        HAVING times_ordered > 0
        ORDER BY times_ordered DESC
    """
    replenishment_history = execute_query(query_replenishment)

    return render_template('admin_templates/reports.html',
                         last_month_sales=last_month_sales,
                         top_customers=top_customers or [],
                         top_books=top_books or [],
                         replenishment_history=replenishment_history or [])


@admin_bp.route('/daily_sales_report', methods=['POST'])
@login_required
@admin_required
def daily_sales_report():
    """Get sales for a specific date"""
    report_date = request.form.get('report_date')

    query = """
        SELECT COALESCE(SUM(Total_Amount), 0) as daily_sales
        FROM SALES_TRANSACTION
        WHERE DATE(Transaction_Date) = %s
    """
    result = execute_query(query, (report_date,), fetch_one=True)
    daily_sales = result['daily_sales'] if result else 0

    flash(f'Sales for {report_date}: ${daily_sales:.2f}', 'info')
    return redirect(url_for('admin.reports'))

