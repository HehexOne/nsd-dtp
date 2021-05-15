USE nsd;

DROP TABLE Agent, Operator, DigitalAssetToken, DigitalAsset, Client;

CREATE TABLE Client (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(256),
    inn VARCHAR(12) UNIQUE,
    email VARCHAR(128) UNIQUE,
    password_hash VARCHAR(256),
    balance FLOAT DEFAULT 0.0,
    is_issuer BOOLEAN DEFAULT FALSE,
    is_approved BOOLEAN DEFAULT FALSE,
    is_banned BOOLEAN DEFAULT FALSE
);

CREATE TABLE DigitalAsset (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(256),
    balance FLOAT,
    quantity INT UNSIGNED,
    due_to DATETIME,
    is_approved BOOLEAN DEFAULT FALSE,
    owner_id INT UNSIGNED,
    holder_id INT UNSIGNED,
    FOREIGN KEY (holder_id) REFERENCES Client(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (owner_id) REFERENCES Client(id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE DigitalAssetToken (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    token VARCHAR(512),
    parent_asset INT UNSIGNED,
    FOREIGN KEY (parent_asset) REFERENCES DigitalAsset(id)
);

CREATE TABLE Operator (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(128),
    surname VARCHAR(128),
    email VARCHAR(128),
    password_hash VARCHAR(256)
);

CREATE TABLE Agent (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(64),
    email VARCHAR(128),
    password_hash VARCHAR(256)
)