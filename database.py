import re
import sqlite3
from datetime import datetime

DB_NAME = "books.db"
BOOKS_TABLE_NAME = "books"
USERS_TABLE_NAME = "users"
CREATE_BOOKS_PATH = "./create_books.sql"
CREATE_USERS_PATH = "./create_users.sql"
DATA_PATH = "./data/books.csv"

class DB:
    def __init__(self):
        self.con = sqlite3.connect(DB_NAME)
        self.num_books = 0

        self.create_users_table()
        self.create_books_table()
        self.add_data()
        #self.count_rows()

    def close_library(self):
        self.con.close()

    def create_users_table(self):
        """
        Calls the create_users.sql file to create a table to contain user info.
        """
        cur = self.con.cursor()
        try:
            with open(CREATE_USERS_PATH, "r") as script:
                cur.executescript(script.read())
                self.con.commit()
            print("Users table created.")
        except:
            print("Failed to create table.")
        return

    def create_books_table(self):
        """
        Calls the create_books.sql file to create table.
        """

        cur = self.con.cursor()
        try:
            with open(CREATE_BOOKS_PATH, "r") as script:
                cur.executescript(script.read())
                self.con.commit()
            print("Books table created.")
        except:
            print("Failed to create table.")
        return


    def add_data(self):
        """
        Inserts data from csv into database.
        """
        cur = self.con.cursor()
        data = []

        with open(DATA_PATH, mode='r') as file:
            for line in file:
                line = line.strip()
                row = re.split(r'(?!\s),(?!\s)',line)
                if len(row) != 12:
                    row = list(filter(None, row))
                row.append(0)
                data.append(row)

        # remove header row
        data = data[1:]
        try:
            insert_records = f"""INSERT INTO {BOOKS_TABLE_NAME} (
                bookID, title, authors, average_rating, isbn, isbn13, language_code,
                num_pages, ratings_count, text_reviews, publication_date, publisher, checked_out
                ) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            cur.executemany(insert_records, data)
            self.con.commit()
            print("Data added.")
        except sqlite3.Error as e:
            print("Failed to add data.")
            print(e)

        return

    def count_rows(self):
        """
        Shows how many entries were inserted into table.
        """
        cur = self.con.cursor()
        q = f"SELECT COUNT(*) FROM {BOOKS_TABLE_NAME}"
        cur.execute(q)
        rv = cur.fetchone()
        self.num_books = rv[0]
        print(f"There are {rv[0]} books in the library.")
        return rv[0]

    def check_user(self, user_name):
        """
        Checks to see if a user exists, and if not, inserts them into the users table.
        """
        cur = self.con.cursor()

        insert_user_query = f"""INSERT OR IGNORE INTO {USERS_TABLE_NAME} VALUES(
            :user_name, :num_checked_out)"""

        try: 
            cur.execute(insert_user_query, {"user_name": user_name, "num_checked_out": 0})
            print(f"Success! Created user. Hello {user_name}")
            return True
        except sqlite3.Error as e:
            print(e)
            print("Could not create user.")
            return False


    def pull_titles(self, search_col):
        """
        Returns titles.
        """

        cur = self.con.cursor()
        q = f"SELECT {search_col}, title, authors, isbn13 FROM {BOOKS_TABLE_NAME}"
        cur.execute(q)
        rv = cur.fetchall()
        return rv


    def insert_row(self, book_info):
        cur = self.con.cursor()
        q = f"""INSERT INTO {BOOKS_TABLE_NAME} VALUES(
            :title, :authors, :average_rating, :isbn, :isbn13, :language_code,
            :num_pages, :ratings_count, :text_reviews, :publication_date, :publisher, :checked_out
            )"""

        try:
            cur.execute(q, book_info)
            self.con.commit()
            print("Success! Book has been added and checked out to your profile.")
        except sqlite3.Error as e:
            print(e)
            print("Could not add book. Please try again.")


    def set_checked_out(self, ind, userID):
        """
        Sets a book's status as checked out by:
            1. changing a book's value in checked_out = false in the books table
            2. creating a table for the book if it doesn't exist and adding userID
            3. creates a table for user if it doesn't exist and updating the no. of books they have out
        """
        cur = self.con.cursor()
        update_query = f"UPDATE books SET checked_out=1 WHERE rowid=:ind"
        
        # update book to be checked_out in books table
        try:
            cur.execute(update_query, {"ind":ind})
            print("Success! Book status has been updated to checked out.")
        except sqlite3.Error as e:
            print(e)
            print("Could not check out book.")
            return False

        # create a separate table for the book being checked out
        create_query = f"""CREATE TABLE IF NOT EXISTS book_{ind}(
                    user TEXT NOT NULL,
                    check_out_date DATETIME NOT NULL,
                    check_in_date DATETIME)"""
        try:
            cur.execute(create_query)
        except sqlite3.Error as e:
            print(e)
            print("Could not create book table.")
            return False

        # update user information in the created table to show that
        # this user has checked this book out
        d = datetime.now()
        today = d.strftime("%Y-%m-%d %H:%M:%S")

        insert_query = f"""INSERT INTO book_{ind} VALUES(
            :user, :check_out_date, :check_in_date)"""
        try:
            cur.execute(insert_query, {"user":userID, "check_out_date": today, "check_in_date": ""})
        except sqlite3.Error as e:
            print(e)
            print("Could not insert user into book table.")
            return False
        
        # if all three of the above operations completed, then we can 
        # create a user table and commit changes
    
        
        self.check_user(userID)
        rv = self.add_book_to_user(userID)
        if rv:
            self.con.commit()
            return True
        return False


    def add_book_to_user(self, user_name):
        """
        Updates the users table to change the number of books checked out for a given username.
        """
        cur = self.con.cursor()
        update_query = f"""UPDATE {USERS_TABLE_NAME} SET num_checked_out = num_checked_out + 1
                        WHERE user_name = :user_name"""

        try:
            cur.execute(update_query, {"user_name": user_name})
            # self.con.commit()
            print("Updated user's books.")
            return True
        except sqlite3.Error as e:
            print(e)
            print("Could not update user's books.")
            return False


#if __name__ == "__main__":
#    db = DB()

