-- DROP TABLE IF EXISTS users;

CREATE TABLE IF NOT EXISTS users(
    userID TEXT NOT NULL,
    UNIQUE(userID)
);