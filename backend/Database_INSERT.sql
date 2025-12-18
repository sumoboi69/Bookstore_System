--
-- Sample Data Population Script for Order Processing System
--

-- 1. POPULATE PUBLISHERS
------------------------------------------------------------
INSERT INTO PUBLISHER (Name, Address, Phone_Number) VALUES 
('Penguin Random House', '1745 Broadway, New York, NY', '212-782-9000'),
('HarperCollins', '195 Broadway, New York, NY', '212-207-7000'),
('Simon & Schuster', '1230 Avenue of the Americas, New York, NY', '212-698-7000'),
('OReilly Media', '1005 Gravenstein Hwy N, Sebastopol, CA', '800-998-9938'),
('Pearson Education', '330 Hudson St, New York, NY', '212-641-2400');

-- 2. POPULATE AUTHORS
------------------------------------------------------------
INSERT INTO AUTHOR (First_Name, Last_Name) VALUES 
('Isaac', 'Asimov'),
('Carl', 'Sagan'),
('Yuval Noah', 'Harari'),
('Stephen', 'Hawking'),
('Neil', 'Gaiman'),
('J.K.', 'Rowling'),
('Walter', 'Isaacson'),
('Donald', 'Knuth');

-- 3. POPULATE BOOKS
-- Note: Publisher_ID references the PUBLISHER table (IDs 1-5 created above)
------------------------------------------------------------
INSERT INTO BOOK (ISBN, Title, Publication_Year, Selling_Price, Category, Publisher_ID, Stock_Quantity, Stock_Threshold) VALUES 
('978-0553293357', 'Foundation', 1951, 8.99, 'Science', 1, 100, 10),
('978-0345391803', 'The Hitchhikers Guide to the Galaxy', 1979, 7.99, 'Science', 1, 15, 5), -- Low stock example
('978-0062316097', 'Sapiens: A Brief History of Humankind', 2011, 22.99, 'History', 2, 60, 10),
('978-0743273565', 'The Great Gatsby', 1925, 10.99, 'Art', 3, 200, 20),
('978-0596520687', 'High Performance Web Sites', 2007, 29.99, 'Science', 4, 40, 5),
('978-0131103627', 'The C Programming Language', 1988, 55.00, 'Science', 5, 30, 5),
('978-1400079988', 'War and Peace', 1869, 14.50, 'History', 1, 5, 10); -- Below threshold (will trigger order on update)

-- 4. LINK BOOKS TO AUTHORS
------------------------------------------------------------
INSERT INTO BOOK_AUTHOR (ISBN, Author_ID) VALUES 
('978-0553293357', 1), -- Foundation by Asimov
('978-0062316097', 3), -- Sapiens by Harari
('978-0131103627', 8); -- C Lang by Knuth

-- 5. POPULATE USERS (ADMINS AND CUSTOMERS)
-- Step 5a: Create USER_ACCOUNT records first
------------------------------------------------------------
INSERT INTO USER_ACCOUNT (Username, Password, Last_Name, First_Name, Email_Address, Phone_Number, Shipping_Address, Account_Type) VALUES 
-- Admin User
('admin_alice', 'securepass1', 'Wonder', 'Alice', 'alice@bookstore.com', NULL, NULL, 'Admin'),

-- Customer User 1
('cust_bob', 'securepass2', 'Builder', 'Bob', 'bob@gmail.com', '555-0101', '123 Construction Ln, Builder City', 'Customer'),

-- Customer User 2
('cust_charlie', 'securepass3', 'Chocolate', 'Charlie', 'charlie@factory.com', '555-0202', '456 Sweet St, Candy Town', 'Customer');

-- Step 5b: Create Subclass records (ADMIN and CUSTOMER)
------------------------------------------------------------
INSERT INTO ADMIN (Username) VALUES ('admin_alice');

INSERT INTO CUSTOMER (Username) VALUES ('cust_bob');
INSERT INTO CUSTOMER (Username) VALUES ('cust_charlie');

-- 6. SHOPPING CARTS
------------------------------------------------------------
-- Create a cart for Bob and Charlie
INSERT INTO SHOPPING_CART (Customer_Username) VALUES ('cust_bob');
INSERT INTO SHOPPING_CART (Customer_Username) VALUES ('cust_charlie');

-- Add items to Bob's cart (Cart ID 1 assumed)
-- Adding 'Foundation' and 'Sapiens'
INSERT INTO CART_ITEM (Cart_ID, ISBN, Quantity) VALUES 
(1, '978-0553293357', 1),
(1, '978-0062316097', 2);

-- 7. SIMULATE A PAST SALE (TRANSACTION)
------------------------------------------------------------
INSERT INTO SALES_TRANSACTION (Customer_Username, Transaction_Date, Total_Amount, Credit_Card_Number, Expiry_Date) VALUES 
('cust_charlie', NOW(), 38.98, '1234567890123456', '12/26');

-- Link items to that sale (Charlie bought 2 copies of Hitchhiker's Guide)
-- Assuming Transaction ID is 1
INSERT INTO SALE_ITEM (Transaction_ID, ISBN, Quantity_Sold, Price_At_Sale) VALUES 
(1, '978-0345391803', 2, 15.98);

-- 8. SIMULATE A PUBLISHER ORDER
------------------------------------------------------------
INSERT INTO PUBLISHER_ORDER (Order_Date, Publisher_ID, Order_Status) VALUES 
(NOW(), 1, 'Confirmed');

INSERT INTO ORDER_ITEM (Order_ID, ISBN, Quantity_Ordered) VALUES 
(1, '978-0553293357', 50);