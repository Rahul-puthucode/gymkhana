-- GYMKHANA Gym Management & Fitness Tracking System Schema

CREATE DATABASE IF NOT EXISTS gymkhana_db;
USE gymkhana_db;

-- Roles table
CREATE TABLE IF NOT EXISTS roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    gender VARCHAR(15),
    date_of_birth DATE,
    height DECIMAL(5, 2),
    weight DECIMAL(5, 2),
    address TEXT,
    emergency_contact VARCHAR(100),
    profile_image VARCHAR(255) DEFAULT 'default_profile.png',
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT
);

-- Trainers table
CREATE TABLE IF NOT EXISTS trainers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    specialization VARCHAR(150),
    experience VARCHAR(50),
    qualification VARCHAR(150),
    status VARCHAR(20) DEFAULT 'active',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Membership Plans table
CREATE TABLE IF NOT EXISTS membership_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    duration_months INT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    benefits TEXT,
    status VARCHAR(20) DEFAULT 'active'
);

-- Subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    plan_id INT NOT NULL,
    start_date DATE NOT NULL,
    expiry_date DATE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES membership_plans(id) ON DELETE RESTRICT
);

-- Subscription History table
CREATE TABLE IF NOT EXISTS subscription_history (
    id INT AUTO_INCREMENT PRIMARY KEY,
    subscription_id INT NOT NULL,
    member_id INT NOT NULL,
    plan_id INT NOT NULL,
    action VARCHAR(50) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (plan_id) REFERENCES membership_plans(id) ON DELETE RESTRICT
);

-- Exercises table
CREATE TABLE IF NOT EXISTS exercises (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    muscle_group VARCHAR(50) NOT NULL,
    equipment VARCHAR(50),
    instructions TEXT,
    description TEXT
);

-- Workout Plans table
CREATE TABLE IF NOT EXISTS workout_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    trainer_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (trainer_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Workout Exercises table
CREATE TABLE IF NOT EXISTS workout_exercises (
    id INT AUTO_INCREMENT PRIMARY KEY,
    workout_plan_id INT NOT NULL,
    exercise_id INT NOT NULL,
    day VARCHAR(20) NOT NULL,
    sets INT NOT NULL,
    reps VARCHAR(30) NOT NULL,
    weight VARCHAR(30),
    rest_seconds INT DEFAULT 60,
    instructions TEXT,
    FOREIGN KEY (workout_plan_id) REFERENCES workout_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE RESTRICT
);

-- Workout Progress table
CREATE TABLE IF NOT EXISTS workout_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    workout_exercise_id INT NOT NULL,
    completed TINYINT(1) DEFAULT 0,
    actual_weight DECIMAL(5, 2),
    actual_reps INT,
    completed_at DATE NOT NULL,
    FOREIGN KEY (member_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (workout_exercise_id) REFERENCES workout_exercises(id) ON DELETE CASCADE
);

-- Diet Plans table
CREATE TABLE IF NOT EXISTS diet_plans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    trainer_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    goal VARCHAR(100),
    calories INT NOT NULL,
    protein INT NOT NULL,
    carbohydrates INT NOT NULL,
    fat INT NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    FOREIGN KEY (member_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (trainer_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Diet Meals table
CREATE TABLE IF NOT EXISTS diet_meals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    diet_plan_id INT NOT NULL,
    meal_type VARCHAR(50) NOT NULL,
    food_name VARCHAR(100) NOT NULL,
    quantity VARCHAR(50) NOT NULL,
    calories INT NOT NULL,
    protein INT DEFAULT 0,
    carbohydrates INT DEFAULT 0,
    fat INT DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (diet_plan_id) REFERENCES diet_plans(id) ON DELETE CASCADE
);

-- Fitness Progress table
CREATE TABLE IF NOT EXISTS fitness_progress (
    id INT AUTO_INCREMENT PRIMARY KEY,
    member_id INT NOT NULL,
    weight DECIMAL(5, 2) NOT NULL,
    height DECIMAL(5, 2) NOT NULL,
    bmi DECIMAL(5, 2) NOT NULL,
    chest DECIMAL(5, 2),
    waist DECIMAL(5, 2),
    arms DECIMAL(5, 2),
    thighs DECIMAL(5, 2),
    recorded_at DATE NOT NULL,
    FOREIGN KEY (member_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Gym Branches table
CREATE TABLE IF NOT EXISTS gym_branches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT NOT NULL,
    phone VARCHAR(20) NOT NULL,
    opening_hours VARCHAR(100) NOT NULL,
    facilities TEXT,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    status VARCHAR(20) DEFAULT 'active'
);

-- Notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'info',
    is_read TINYINT(1) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Activity Logs table
CREATE TABLE IF NOT EXISTS activity_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    role VARCHAR(20),
    action VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);
