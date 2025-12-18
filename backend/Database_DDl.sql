--
-- Database DDL for Order Processing System (Online Bookstore) - Fall 2025
--

-- 1. DROP TABLES (for easy re-running of the script)
DROP TABLE IF EXISTS SALE_ITEM;
DROP TABLE IF EXISTS SALES_TRANSACTION;
DROP TABLE IF EXISTS CART_ITEM;
DROP TABLE IF EXISTS SHOPPING_CART;
DROP TABLE IF EXISTS ORDER_ITEM;
DROP TABLE IF EXISTS PUBLISHER_ORDER;
DROP TABLE IF EXISTS BOOK_AUTHOR;
DROP TABLE IF EXISTS AUTHOR;
DROP TABLE IF EXISTS BOOK;
DROP TABLE IF EXISTS PUBLISHER;
DROP TABLE IF EXISTS CUSTOMER;
DROP TABLE IF EXISTS ADMIN;
DROP TABLE IF EXISTS USER_ACCOUNT;

-- 2. CORE SYSTEM ENTITIES
------------------------------------------------------------

-- PUBLISHER
CREATE TABLE PUBLISHER (
    Publisher_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(255) NOT NULL UNIQUE,
    Address VARCHAR(255),
    Phone_Number VARCHAR(20)
);

-- BOOK
CREATE TABLE BOOK (
    ISBN VARCHAR(20) PRIMARY KEY,
    Title VARCHAR(255) NOT NULL,
    Publication_Year YEAR,
    Selling_Price DECIMAL(10, 2) NOT NULL CHECK (Selling_Price >= 0),
    Category ENUM('Science', 'Art', 'Religion', 'History', 'Geography') NOT NULL,
    Publisher_ID INT NOT NULL,
    Stock_Quantity INT NOT NULL DEFAULT 0 CHECK (Stock_Quantity >= 0),
    Stock_Threshold INT NOT NULL CHECK (Stock_Threshold > 0), -- Minimum quantity to be maintained
    FOREIGN KEY (Publisher_ID) REFERENCES PUBLISHER(Publisher_ID)
);

-- AUTHOR
CREATE TABLE AUTHOR (
    Author_ID INT AUTO_INCREMENT PRIMARY KEY,
    First_Name VARCHAR(100) NOT NULL,
    Last_Name VARCHAR(100) NOT NULL
);

-- BOOK_AUTHOR (Many-to-Many relationship)
CREATE TABLE BOOK_AUTHOR (
    ISBN VARCHAR(20) NOT NULL,
    Author_ID INT NOT NULL,
    PRIMARY KEY (ISBN, Author_ID),
    FOREIGN KEY (ISBN) REFERENCES BOOK(ISBN),
    FOREIGN KEY (Author_ID) REFERENCES AUTHOR(Author_ID)
);

-- 3. USER AND ACCOUNT MANAGEMENT
------------------------------------------------------------

-- USER_ACCOUNT
CREATE TABLE USER_ACCOUNT (
    Username VARCHAR(50) PRIMARY KEY,
    Password VARCHAR(255) NOT NULL,
    Last_Name VARCHAR(100) NOT NULL,
    First_Name VARCHAR(100) NOT NULL,
    Email_Address VARCHAR(100) UNIQUE NOT NULL,
    Phone_Number VARCHAR(20),
    Shipping_Address VARCHAR(255),
    Account_Type ENUM('Admin', 'Customer') NOT NULL -- Differentiates user types
);

-- CUSTOMER
CREATE TABLE CUSTOMER (
    Username VARCHAR(50) PRIMARY KEY,
    FOREIGN KEY (Username) REFERENCES USER_ACCOUNT(Username) ON DELETE CASCADE
);

-- ADMIN
CREATE TABLE ADMIN (
    Username VARCHAR(50) PRIMARY KEY,
    FOREIGN KEY (Username) REFERENCES USER_ACCOUNT(Username) ON DELETE CASCADE
);

-- 4. PUBLISHER ORDERS (REPLENISHMENT)
------------------------------------------------------------

-- PUBLISHER_ORDER
CREATE TABLE PUBLISHER_ORDER (
    Order_ID INT AUTO_INCREMENT PRIMARY KEY,
    Order_Date DATETIME NOT NULL,
    Publisher_ID INT NOT NULL,
    Order_Status ENUM('Pending', 'Confirmed') NOT NULL DEFAULT 'Pending',
    FOREIGN KEY (Publisher_ID) REFERENCES PUBLISHER(Publisher_ID)
);

-- ORDER_ITEM
CREATE TABLE ORDER_ITEM (
    Order_ID INT NOT NULL,
    ISBN VARCHAR(20) NOT NULL,
    Quantity_Ordered INT NOT NULL CHECK (Quantity_Ordered > 0),
    PRIMARY KEY (Order_ID, ISBN),
    FOREIGN KEY (Order_ID) REFERENCES PUBLISHER_ORDER(Order_ID),
    FOREIGN KEY (ISBN) REFERENCES BOOK(ISBN)
);

-- 5. CUSTOMER SHOPPING AND SALES
------------------------------------------------------------

-- SHOPPING_CART
CREATE TABLE SHOPPING_CART (
    Cart_ID INT AUTO_INCREMENT PRIMARY KEY,
    Customer_Username VARCHAR(50) NOT NULL UNIQUE, -- One cart per customer
    FOREIGN KEY (Customer_Username) REFERENCES CUSTOMER(Username) ON DELETE CASCADE
);

-- CART_ITEM
CREATE TABLE CART_ITEM (
    Cart_ID INT NOT NULL,
    ISBN VARCHAR(20) NOT NULL,
    Quantity INT NOT NULL CHECK (Quantity > 0),
    PRIMARY KEY (Cart_ID, ISBN),
    FOREIGN KEY (Cart_ID) REFERENCES SHOPPING_CART(Cart_ID) ON DELETE CASCADE,
    FOREIGN KEY (ISBN) REFERENCES BOOK(ISBN)
);

-- SALES_TRANSACTION
CREATE TABLE SALES_TRANSACTION (
    Transaction_ID INT AUTO_INCREMENT PRIMARY KEY,
    Customer_Username VARCHAR(50) NOT NULL,
    Transaction_Date DATETIME NOT NULL,
    Total_Amount DECIMAL(10, 2) NOT NULL CHECK (Total_Amount >= 0),
    Credit_Card_Number VARCHAR(16) NOT NULL, -- Simplified storage for project
    Expiry_Date VARCHAR(5) NOT NULL, -- Simplified storage (MM/YY)
    FOREIGN KEY (Customer_Username) REFERENCES CUSTOMER(Username)
);

-- SALE_ITEM
CREATE TABLE SALE_ITEM (
    Transaction_ID INT NOT NULL,
    ISBN VARCHAR(20) NOT NULL,
    Quantity_Sold INT NOT NULL CHECK (Quantity_Sold > 0),
    Price_At_Sale DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (Transaction_ID, ISBN),
    FOREIGN KEY (Transaction_ID) REFERENCES SALES_TRANSACTION(Transaction_ID) ON DELETE CASCADE,
    FOREIGN KEY (ISBN) REFERENCES BOOK(ISBN)
);

-- 6. TRIGGERS (for business logic and integrity)
------------------------------------------------------------

-- TRIGGER 1: Prevent negative stock quantity on update/sale (Hint: trigger before update)
DELIMITER //
CREATE TRIGGER before_book_stock_update
BEFORE UPDATE ON BOOK
FOR EACH ROW
BEGIN
    IF NEW.Stock_Quantity < 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ERROR: Stock quantity cannot be negative.';
    END IF;
END;
//
DELIMITER ;

-- TRIGGER 2: Automatic replenishment order placement (Hint: trigger after update on books table)
-- This trigger places an order for a fixed quantity (e.g., 50 copies) if the stock drops below the threshold.
DELIMITER //
CREATE TRIGGER after_book_stock_check
AFTER UPDATE ON BOOK
FOR EACH ROW
BEGIN
    -- Check if the quantity dropped from above the threshold to below or at the threshold
    IF OLD.Stock_Quantity > OLD.Stock_Threshold AND NEW.Stock_Quantity <= NEW.Stock_Threshold THEN
        
        -- Define the constant order quantity
        SET @OrderQuantity = 50; 
        
        -- Insert a new pending order into PUBLISHER_ORDER
        INSERT INTO PUBLISHER_ORDER (Order_Date, Publisher_ID, Order_Status)
        VALUES (NOW(), NEW.Publisher_ID, 'Pending');
        
        -- Get the ID of the new order
        SET @NewOrderID = LAST_INSERT_ID();
        
        -- Insert the book and fixed quantity into ORDER_ITEM
        INSERT INTO ORDER_ITEM (Order_ID, ISBN, Quantity_Ordered)
        VALUES (@NewOrderID, NEW.ISBN, @OrderQuantity);
    END IF;
END;
//
DELIMITER ;

-- TRIGGER 3: Update stock quantity upon Admin Order Confirmation
DELIMITER //
CREATE TRIGGER after_order_confirmed
AFTER UPDATE ON PUBLISHER_ORDER
FOR EACH ROW
BEGIN
    -- Check if the status changed to 'Confirmed'
    IF OLD.Order_Status = 'Pending' AND NEW.Order_Status = 'Confirmed' THEN
        -- Iterate through all items in the confirmed order
        UPDATE BOOK b
        JOIN ORDER_ITEM oi ON b.ISBN = oi.ISBN
        SET b.Stock_Quantity = b.Stock_Quantity + oi.Quantity_Ordered -- Add ordered quantity to stock
        WHERE oi.Order_ID = NEW.Order_ID;
    END IF;
END;
//
DELIMITER ;

-- TRIGGER 4: Remove all items from shopping cart upon Customer Logout
DELIMITER //
CREATE TRIGGER before_customer_logout
BEFORE DELETE ON CUSTOMER
FOR EACH ROW
BEGIN
    -- Deleting the CUSTOMER record (via the cascading delete from USER_ACCOUNT)
    -- will trigger this, so we use it to clean up the cart items associated with that customer.
    DELETE ci
    FROM CART_ITEM ci
    JOIN SHOPPING_CART sc ON ci.Cart_ID = sc.Cart_ID
    WHERE sc.Customer_Username = OLD.Username;
END;
//
DELIMITER ;