CREATE DATABASE service_marketplace;
USE service_marketplace;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    password VARCHAR(100)
);

CREATE TABLE providers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    service_type VARCHAR(100),
    experience INT,
    address VARCHAR(255),
    password VARCHAR(100)
);

CREATE TABLE services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(100)
);

INSERT INTO services (service_name) VALUES
('Electrician'),
('Plumber'),
('Cleaning'),
('Beauty'),
('AC Repair'),
('Painting');

CREATE TABLE bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    provider_id INT,
    service_name VARCHAR(100),
    date DATE,
    time TIME,
    address VARCHAR(255),
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'Pending'
);

CREATE TABLE admin (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE,
    password VARCHAR(100)
);

INSERT INTO admin (username, password)
VALUES ('admin', 'admin123');

