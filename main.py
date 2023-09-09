from database import DB
import jaro
from collections import defaultdict
import random

class Library:

    def __init__(self):
        self.db = DB()
        self.num_books = self.db.count_rows()
        self.num_checked_out = 0
        self.cur_user = None


    def checkout_book(self):
        """
        Creates a new Book object and adds it to catalogue
        """
        r = input("Would you like to search using a title, author, or ISBN13? ")
        if r.lower() == "title":
            title = input("Please provide the title: ")
            rv = self.search_book(title=title)
        elif r.lower() == "author":
            author = input("Please provide the author: ")
            rv = self.search_book(author=author)
        elif r.lower() == "isbn13":
            isbn13 = input("Please provide the isbn13: ")
            rv = self.search_book(isbn13=isbn13)
        else:
            print("Please provide a valid title, author, or ISBN13. ")
            return 

        if not rv:
            redo = input("Would you like to do another search? (Y/N) ")
            if redo == "Y" or redo == "y":
                return
            self.make_book()
        inds, menu = rv
        print("Search results: title | author | isbn13")

        # display search results
        for i in range(1, len(menu)+1):
            print(f"{i}. {menu[i-1]}")
        print(f"{len(menu)+1}. My book isn't on the list.")

        # user provides input
        resp = input("Make selection: ")
        try:
            resp = int(resp)
            assert 1 <= resp <= len(menu)+1
        except ValueError:
            print("Please provide a valid input")
            return
        except AssertionError:
            print("Please provide a value within range.")
            return

        if resp==len(menu)+1:
            redo = input("Would you like to do another search? (Y/N) ")
            if redo == "Y" or redo == "y":
                return
            self.make_book()
        else:
            self.set_book_out(inds[resp-1])


    def search_book(self, title=None, author=None, isbn13=None):
        """
        Searches for a book in the DB. Calls quicksort helper function
        and uses jaro-winkler fuzzy matching to find similar search criteria.
        """
        MATCH = 0.85
        menu = []
        inds = []
        rv = []
        probs_titles = defaultdict(list)
    
        if title:
            rv = self.db.pull_titles("title")
        elif author:
            rv =  self.db.pull_titles("authors")
        elif isbn13:
            rv = self.db.pull_titles("isbn13")
    
        search_term = title or author or isbn13

        for i in range(len(rv)):
            prob = jaro.jaro_winkler_metric(search_term, rv[i][0])
            if prob >= MATCH:
                probs_titles[prob].append((rv[i][1], rv[i][2], rv[i][3], rv[i][4]))
        if len(probs_titles) < 1:
            return

        probs = list(probs_titles.keys())
        self.quicksort(probs, 0, len(probs)-1)

        for i in range(len(probs)-1, -1, -1):
            for p in probs_titles[probs[i]]:
                entry = [p[0], p[1], str(p[2])]
                entry = " | ".join(entry)
                menu.append(entry)
                inds.append(p[3])

        return inds, menu


    def make_book(self):
        """
        Adds a new book to the DB.
        """
        resp = input("We don't seem to have that book. Would you like to add it? Y/N")
        if resp != "Y" and resp != "N":
            print("Please provide a valid response.")
            return
        elif resp == "N":
            print("Please come again.")

        # ask user for inputs
        title = input("What's the title of your book? ")
        
        authors = input("Who are the author(s) of the book? ")
        isbn13 = input("What is the book's isbn13 number? ")
    
        rv = {
            "title": title,
            "authors": authors,
            "average_rating" : "",
            "isbn13" : isbn13,
            "isbn": "",
            "language_code": "",
            "num_pages": "",
            "ratings_count": "",
            "text_reviews": "",
            "publication_date": "",
            "publisher": "",
            "checked_out": 1}

        self.db.insert_row(rv)
        return

    def set_book_out(self, ind):
        """
        Calls db functions to change a book's status as checked out.
        """
        rv = self.db.check_book_out(ind, self.cur_user)
        if not rv:
            print("Could not check out book.")
        print("Book successfully checked out.")
        return


    def create_user(self):
        """
        Creates user based on provided username.
        """
        rv = self.db.create_user(self.cur_user)
        print(f"User successfully created. Welcome, {self.cur_user}")
        return rv


    def get_user_info(self):
        """
        Retrieves books that the current user has out.
        """
        print("Retrieving user info...")
        rv = self.db.get_user_info(self.cur_user)
        if not rv:
            print("You have no books out.")
            return
        print("Here is your information: ")
        print(f"You currently have {len(rv)} books out.")
        for i in range(1, len(rv)+1):
            print(f"{i}. {rv[i-1][1]}")
        return rv


    def checkin_book(self):
        """
        Check book in when a user returns it.
        """
        rv = self.get_user_info()
        if not rv:
            print("You have no books out.")
            return
        print(rv)
        resp = input("Which book would you like to return? ")
        try:
            resp = int(resp)
            assert 1 <= resp <= len(rv)
        except ValueError:
            print("Please provide a valid response.")
            return False
        except AssertionError:
            print("Please provide a value within range.")
            return False

        self.db.return_book(rv[resp-1][0], self.cur_user)
        print("Book successfully checked in.")
        return True


    def pivot(self, probs, lb, ub):
        """
        Helper function for quicksort function.
        """

        if lb >= ub:
            return lb 
        pivot = probs[lb]
        i = lb
        j = ub

        while i < j:
            while probs[i] < pivot and i < ub:
                i += 1
            while probs[j] >= pivot and j > lb:
                j -= 1
            if i <= j and probs[i] > probs[j]:
                probs[i], probs[j] = probs[j], probs[i]
                i += 1
                j -= 1
        probs[lb], probs[j] = probs[j], probs[lb]
        return j


    def quicksort(self, probs, lb, ub):
        """
        Quicksort function to sort probabilities.
        """

        if lb < ub:
            part = self.pivot(probs, lb, ub)
            if part < lb:
                return
            self.quicksort(probs, lb, part)
            self.quicksort(probs, part+1, ub)


def go():
    library = Library()
    

    # get username from user
    user_name = input("Hello, what's your userID? ")
    if not user_name:
        print("Error, please enter a valid userID.")
        return
    library.cur_user = user_name
    user_set = library.create_user()
    if not user_set:
        print("Error, could not set userID. Please try again.")
        return
            

    while True:
        opts = {
            1: "Check out a book",
            2: "Check in a book",
            3: "View my info",
            4: "Leave"
        }

        print('What would you like to do today\n')
        for key, val in opts.items():
            print(f"{key}. {val}")
        rv = input("\nPlease enter a number: ")
        print("You entered: ", rv)
        try:
            rv = int(rv)
            assert 1<= rv <= 4
        except ValueError as e:
            print(e)
            print("Please enter a number between 1 and 4. ")
        except AssertionError:
            print("Please enter a value within range.")

        if rv == 1:
            library.checkout_book()
        elif rv == 2:
            library.checkin_book()
        elif rv == 3:
            library.get_user_info()
        elif rv == 4:
            print("Please come again.")
            break
    
    library.db.close_library()

if __name__ == "__main__":
    go()
