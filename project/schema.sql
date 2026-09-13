-- Production Database Schema for OTP Authentication API

CREATE DATABASE IF NOT EXISTS `try-fit` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `try-fit`;

-- Users Table
CREATE TABLE IF NOT EXISTS `users` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `full_name` VARCHAR(100) NOT NULL,
    `email` VARCHAR(150) NOT NULL UNIQUE,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- OTP Verification Table
CREATE TABLE IF NOT EXISTS `otp_verification` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `email` VARCHAR(150) NOT NULL,
    `otp_hash` VARCHAR(128) NOT NULL,
    `expires_at` DATETIME NOT NULL,
    `attempts` INT DEFAULT 0,
    `verified` BOOLEAN DEFAULT FALSE,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_otp_email` (`email`),
    INDEX `idx_otp_email_verified` (`email`, `verified`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Clothes Table (Referenced by Order Items)
CREATE TABLE IF NOT EXISTS `clothes` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    `category` VARCHAR(100) NOT NULL,
    `price` DECIMAL(10, 2) NOT NULL,
    `trial_price` DECIMAL(10, 2) NOT NULL,
    `image_url` VARCHAR(255) NOT NULL,
    `brand` VARCHAR(100) DEFAULT 'TRY-FIT',
    `description` TEXT,
    `rating` DECIMAL(3, 1) DEFAULT 4.5,
    `discount_percent` INT DEFAULT 0,
    `available_sizes` VARCHAR(255) DEFAULT 'S,M,L,XL',
    `available_colors` VARCHAR(255) DEFAULT 'Black,White'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Orders Table
CREATE TABLE IF NOT EXISTS `orders` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL,
    `customer_name` VARCHAR(100) NULL,
    `total_amount` DECIMAL(10, 2) NOT NULL,
    `discount_amount` DECIMAL(10, 2) DEFAULT 0,
    `trial_charges` DECIMAL(10, 2) DEFAULT 0,
    `delivery_charges` DECIMAL(10, 2) DEFAULT 0,
    `final_total` DECIMAL(10, 2) NOT NULL,
    `status` VARCHAR(50) DEFAULT 'Pending',
    `delivery_address` TEXT NOT NULL,
    `payment_method` VARCHAR(50) DEFAULT 'Cash on Delivery',
    `razorpay_order_id` VARCHAR(255) NULL,
    `razorpay_payment_id` VARCHAR(255) NULL,
    `razorpay_signature` VARCHAR(255) NULL,
    `payment_status` ENUM('created','paid','failed') DEFAULT 'created',
    `payment_verified_at` DATETIME NULL,
    `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_orders_user_id` (`user_id`),
    FOREIGN KEY (`user_id`)
        REFERENCES `users`(`id`)
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Order Items Table
CREATE TABLE IF NOT EXISTS `order_items` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `order_id` INT NOT NULL,
    `cloth_id` INT NOT NULL,
    `quantity` INT DEFAULT 1,
    `price` DECIMAL(10, 2) NOT NULL,
    `size` VARCHAR(20) NOT NULL,
    `color` VARCHAR(50) NOT NULL,
    INDEX `idx_order_items_order_id` (`order_id`),
    INDEX `idx_order_items_cloth_id` (`cloth_id`),
    FOREIGN KEY (`order_id`)
        REFERENCES `orders`(`id`)
        ON DELETE CASCADE,
    FOREIGN KEY (`cloth_id`)
        REFERENCES `clothes`(`id`)
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
