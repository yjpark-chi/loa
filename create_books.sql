DROP TABLE IF EXISTS books;

CREATE TABLE books(
    bookID TEXT NOT NULL,
    title TEXT NOT NULL,
    authors TEXT,
    average_rating REAL,
    isbn TEXT NOT NULL,
    isbn13 INTEGER NOT NULL,
    language_code TEXT,
    num_pages INTEGER,
    ratings_count INTEGER,
    text_reviews INTEGER,
    publication_date DATE,
    publisher TEXT,
    checked_out INTEGER NOT NULL
);