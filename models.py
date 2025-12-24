"""
Models for the Bookstore System
We use Flask-Login for authentication but don't use SQLAlchemy ORM
Instead, we use direct database queries with pymysql
"""
from flask_login import UserMixin
from extensions import login_manager
from database import execute_query


class User(UserMixin):
    """User model for Flask-Login authentication"""

    def __init__(self, username, password, first_name, last_name, email, phone, address, account_type):
        self.id = username  # Flask-Login uses 'id' attribute
        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.address = address
        self.account_type = account_type

    @property
    def fullname(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_admin(self):
        return self.account_type == 'Admin'

    @property
    def is_customer(self):
        return self.account_type == 'Customer'

    @staticmethod
    def get_by_username(username):
        """Fetch user by username from database"""
        query = """
            SELECT Username, Password, First_Name, Last_Name, Email_Address, 
                   Phone_Number, Shipping_Address, Account_Type
            FROM USER_ACCOUNT 
            WHERE Username = %s
        """
        result = execute_query(query, (username,), fetch_one=True)

        if result:
            return User(
                username=result['Username'],
                password=result['Password'],
                first_name=result['First_Name'],
                last_name=result['Last_Name'],
                email=result['Email_Address'],
                phone=result['Phone_Number'],
                address=result['Shipping_Address'],
                account_type=result['Account_Type']
            )
        return None

    @staticmethod
    def create_customer(username, password, first_name, last_name, email, phone, address):
        """Create a new customer account"""
        query_user = """
            -- SQL QUERY PLACEHOLDER: Insert new user account
            -- INSERT INTO USER_ACCOUNT (Username, Password, First_Name, Last_Name, Email_Address, Phone_Number, Shipping_Address, Account_Type)
            -- VALUES (%s, %s, %s, %s, %s, %s, %s, 'Customer')
        """
        # TODO: Replace with actual queries

        query_customer = """
            -- SQL QUERY PLACEHOLDER: Insert into CUSTOMER table
            -- INSERT INTO CUSTOMER (Username) VALUES (%s)
        """

        # Execute both queries
        execute_query(query_user, (username, password, first_name, last_name, email, phone, address), commit=True)
        execute_query(query_customer, (username,), commit=True)

        return True


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.get_by_username(user_id)
