USE nsd;

DROP TABLE DigitalAssetToken, DigitalAsset, Client, Operator;

CREATE TABLE Operator (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(128),
    email VARCHAR(128),
    password_hash VARCHAR(256),
    is_banned BOOLEAN DEFAULT FALSE
);

CREATE TABLE Client (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(256),
    inn VARCHAR(12) UNIQUE,
    address VARCHAR(512),
    email VARCHAR(128) UNIQUE,
    password_hash VARCHAR(256),
    balance FLOAT DEFAULT 0.0,
    is_issuer BOOLEAN DEFAULT FALSE,
    is_approved BOOLEAN DEFAULT FALSE,
    is_banned BOOLEAN DEFAULT FALSE,
    who_approve INT UNSIGNED,
    FOREIGN KEY (who_approve) REFERENCES Operator(id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE DigitalAsset (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(256),
    who_approve INT UNSIGNED,
    balance FLOAT,
    percent FLOAT,
    quantity INT UNSIGNED,
    due_to DATETIME,
    is_approved BOOLEAN DEFAULT FALSE,
    is_banned BOOLEAN DEFAULT FALSE,
    owner_id INT UNSIGNED,
    FOREIGN KEY (who_approve) REFERENCES Operator(id) ON UPDATE CASCADE ON DELETE CASCADE,
    FOREIGN KEY (owner_id) REFERENCES Client(id) ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE DigitalAssetToken (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    token VARCHAR(512),
    holder_id INT UNSIGNED,
    parent_asset INT UNSIGNED,
    FOREIGN KEY (parent_asset) REFERENCES DigitalAsset(id),
    FOREIGN KEY (holder_id) REFERENCES Client(id)
);