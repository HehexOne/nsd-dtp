USE nsd;

CREATE TABLE Client (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(256),
    inn VARCHAR(12) UNIQUE,
    email VARCHAR(128) UNIQUE,
    password_hash VARCHAR(256),
    balance FLOAT DEFAULT 0.0,
    is_issuer BOOLEAN DEFAULT FALSE
);

CREATE TABLE DigitalAsset (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(256),
    balance FLOAT,
    token VARCHAR(512),
    is_approved BOOLEAN DEFAULT FALSE,
    owner_id INT UNSIGNED,
    holder INT UNSIGNED,
    FOREIGN KEY (owner_id) REFERENCES Client(id),
    FOREIGN KEY (holder) REFERENCES Client(id)
);

CREATE TABLE Operator (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(128),
    surname VARCHAR(128),
    email VARCHAR(128),
    password_hash VARCHAR(256)
);