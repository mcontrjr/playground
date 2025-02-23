CREATE TABLE IF NOT EXISTS bank_statements (
    id SERIAL PRIMARY KEY,
    bank VARCHAR(255),
    date DATE,
    description TEXT,
    amount DECIMAL(10, 2),
    category VARCHAR(255)
);