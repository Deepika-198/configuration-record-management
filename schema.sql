CREATE TABLE IF NOT EXISTS records (
    id INTEGER NOT NULL AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(80) NOT NULL,
    category VARCHAR(80) NOT NULL,
    status VARCHAR(10) NOT NULL CHECK (status IN ('draft', 'active', 'archived'))
);
