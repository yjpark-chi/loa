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
        """
        Closes the connection to the sqlite table.
        """
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

        # check to see if the books table already exists
        # if so, don't populate it again.
        select_query = f"""SELECT * FROM {BOOKS_TABLE_NAME} LIMIT 1"""
        cur.execute(select_query)
        rv = cur.fetchone()

        if rv:
            print("Data already populated.")
            return

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

        return True


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


    def pull_titles(self, search_col):
        """
        Returns titles based on what user is searching for (search_col).
        """

        cur = self.con.cursor()
        q = f"SELECT {search_col}, title, authors, isbn13, rowid FROM {BOOKS_TABLE_NAME} WHERE checked_out=0"
        cur.execute(q)
        rv = cur.fetchall()
        return rv


    def insert_row(self, book_info):
        """
        Adds row to the books table.
        """
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


    def add_book_to_user(self, user_name, bookID, date_checked_out):
        """
        Adds book information to a user's table to show that a user has checked out a book.
        """
        cur = self.con.cursor()
        insert_query = f"""INSERT INTO user_{user_name} VALUES(
            :bookID, :date_checked_out, :date_checked_in)"""
    
        try:
            cur.execute(insert_query, {"bookID": bookID, "date_checked_out": date_checked_out, "date_checked_in": ""})
            print("Added book to user table.")
            return True
        except sqlite3.Error as e:
            print("Error: couldn't add book to user table.")
            print(e)
            return False


    def set_book_availability(self, ind, checking_out):
        """
        Updates the book table for a certain book to either checked out or available status
            by using the checking_out variable (either 0 or 1).
        """
        cur = self.con.cursor()

        # update books table and set checked_out status
        update_query = f"UPDATE books SET checked_out=:checking_out WHERE rowid=:ind"
        try:
            cur.execute(update_query, {"checking_out": checking_out, "ind": ind})
            print(f"Success! Book status has been updated to {checking_out}.")
            return True
        except sqlite3.Error as e:
            print(e)
            print("Could not check out book.")
            return False


    def create_book(self, ind):
        """
        Creates a separate table for a book being checked out to store
            information about which users have checked it out.
        """
        cur = self.con.cursor()
        # create a separate table for the book being checked out
        create_query = f"""CREATE TABLE IF NOT EXISTS book_{ind}(
                    user TEXT NOT NULL,
                    check_out_date DATETIME NOT NULL,
                    check_in_date DATETIME)"""
        try:
            cur.execute(create_query)
            print("Success, table for book has been created.")
            return True
        except sqlite3.Error as e:
            print(e)
            print("Could not create book table.")
            return False


    def create_user(self, user_name):
        """
        Checks to see if a user exists, and if not, inserts them into the users
            table and creates a separate table using their userID.
        """
        cur = self.con.cursor()

        insert_user_query = f"""INSERT OR IGNORE INTO {USERS_TABLE_NAME} VALUES(
            :userID)"""
        
        create_user_table_query = f"""CREATE TABLE IF NOT EXISTS user_{user_name} (
            bookID TEXT NOT NULL,
            check_out_date DATE,
            check_in_date DATE,
            UNIQUE(bookID, check_out_date))"""

        # insert user as a row in the users table
        try: 
            cur.execute(insert_user_query, {"userID": user_name})
            print(f"Success! Added user {user_name}")
        except sqlite3.Error as e:
            print(e)
            print("Could not create user.")
            return False

        try:
            cur.execute(create_user_table_query, {"userID": user_name})
            print(f"Success! Created table for user {user_name}")
        except sqlite3.Error as e:
            print("Error: could not create table for user.")
            print(e)
            return False

        self.con.commit()
        return True


    def add_user_to_book(self, ind, userID, date_out):
        """
        Adds user info to a table for a book that shows when they checked it out and checked it in.
        """
        cur = self.con.cursor()
        insert_query = f"""INSERT INTO book_{ind} VALUES(
            :user, :check_out_date, :check_in_date)"""
        try:
            cur.execute(insert_query, {"user":userID, "check_out_date": date_out, "check_in_date": ""})
            print("Success, added book to user.")
            return True
        except sqlite3.Error as e:
            print(e)
            print("Could not insert user into book table.")
            return False


    def check_book_out(self, ind, userID):
        """
        Checks out a book by setting the checked_out status in books table = 1, creating a
            table for a book, adding the user to that book, and adding user info to the table for the book.
        """

        d = datetime.now()
        today = d.strftime("%Y-%m-%d %H:%M:%S")

        rv1 = self.set_book_availability(ind, 1)
        rv2 = self.create_book(ind)
        rv3 = self.add_user_to_book(ind, userID, today)

        rv4 = self.add_book_to_user(userID, ind, today)
        if rv1 and rv2 and rv3 and rv4:
            self.con.commit()
            return True
        return False


    def get_user_info(self, userID):
        """
        Retrieves the books a user has checked out.
        """
        cur = self.con.cursor()
        select_query = f"""SELECT u.bookID, books.title, books.authors, u.check_out_date
                        FROM user_{userID} as u 
                        JOIN books ON books.rowid = u.bookID
                        WHERE u.check_in_date="" """
        try:
            cur.execute(select_query, {"userID": userID})
            rv = cur.fetchall()
            return rv
        except sqlite3.Error as e:
            print("Error: could not retrieve user info.")
            print(e)
            return []


    def check_book_in(self, ind, userID):
        """
        Checks book in by updating a book table and the user table with the check in date.
        """
        cur = self.con.cursor()
        d = datetime.now()
        today = d.strftime("%Y-%m-%d %H:%M:%S")

        update_book_query = f"UPDATE book_{ind} SET check_in_date=:check_in_date WHERE user=:userID"
        update_user_query = f"UPDATE user_{userID} SET check_in_date=:check_in_date WHERE bookID=:ind"
        try:
            cur.execute(update_book_query, {"check_in_date": today, "userID": userID})
            print(f"Updated table book_{ind}.")
            cur.execute(update_user_query, {"check_in_date": today, "ind": ind})
            print(f"Updated table user_{userID}.")
            return True
        except sqlite3.Error as e:
            print("Could not check book in from user.")
            print(e)
            return False


    def return_book(self, ind, userID):
        """
        Returns book by calling functions to update a book's status in the books table as checked in
            and updating check in information in the individual user and book table.
        """
        rv1 = self.set_book_availability(ind, 0)
        rv2 = self.check_book_in(ind, userID)
        if rv1 and rv2:
            self.con.commit()
            return True
        else:
            print("Could not return book")
            return False


# if __name__ == "__main__":
#     db = DB()
