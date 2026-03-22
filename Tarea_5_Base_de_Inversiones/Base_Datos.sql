-- SQL content for database setup
CREATE TABLE IF NOT EXISTS Investments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    date DATE NOT NULL
);

-- Add any additional SQL commands here...