-- Create and use the database
CREATE DATABASE IF NOT EXISTS hostel_db;
USE hostel_db;

-- Admin table
CREATE TABLE IF NOT EXISTS admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    password VARCHAR(50) NOT NULL
);

-- Insert default admin
INSERT INTO admin (username, password) VALUES ('admin', 'admin123');

-- Rooms table
CREATE TABLE IF NOT EXISTS rooms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    is_occupied BOOLEAN DEFAULT 0
);

-- Insert 10 rooms
INSERT INTO rooms (is_occupied)
VALUES (0), (0), (0), (0), (0), (0), (0), (0), (0), (0);

-- Students table
CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    password VARCHAR(255) NOT NULL,
    college_id VARCHAR(20),
    amount_payable DECIMAL(10, 2) DEFAULT 0,
    payment_status ENUM('Paid', 'Pending') DEFAULT 'Pending',
    room_id INT,
    check_in DATETIME,
    check_out DATETIME
);

