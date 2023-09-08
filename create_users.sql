DROP TABLE IF EXISTS users;

CREATE TABLE users(
    user_name TEXT NOT NULL,
    num_checked_out INTEGER,
    UNIQUE(user_name)
);