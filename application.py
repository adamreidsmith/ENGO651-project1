import os

from flask import Flask, session, render_template, request, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text
from models import *
import requests

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ['DATABASE_URL']
db.init_app(app)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


# The home page
@app.route("/")
def index():
    if session.get('current_user') is not None:
        session.pop('current_user')
    return render_template("main.html")


# The sign in page 
@app.route("/signin", methods=["GET"])
def sign_in():
    if session.get('current_user') is not None:
        session.pop('current_user')
    return render_template("sign_in.html")


# The sign-up page
@app.route("/signup", methods=["GET"])
def sign_up():
    if session.get('current_user') is not None:
        session.pop('current_user')
    return render_template("sign_up.html")


# Handle the sign-in logic
@app.route("/login", methods=["POST"])
def log_in():
    # Get text from input
    username = request.form.get("username")
    password = request.form.get("password")
    # password2 = request.form.get("password2")

    # Case1: check whether username exists
    username_check = db.execute(text(f"SELECT * FROM users WHERE username='{username}'")).fetchall()

    if len(username_check) == 0:
        # Button should link to sign-up page *
        return render_template('error.html', message="Invalid username.", button="Sign Up", url='signup')
    
    # Case2: wrong password
    password_check = db.execute(text(f"SELECT * FROM users WHERE username='{username}' AND password='{password}'")).fetchall()
    if len(password_check) == 0:
        # Button should link to sign-in page *
        return render_template('error.html', message="Incorrect password.", button="Sign In Again", url='signin')

    # Store current user
    session["current_user"] = username
    
    return render_template('success.html')


# Handle the sign-up logic
@app.route("/login_new", methods=["POST"])
def log_in_new():
    # Get text from input
    username = request.form.get("username")
    password = request.form.get("password")
    password2 = request.form.get("password2")

    # Case1: check whether data has been entered
    if username == '' or password == '':
        # Button should link to sign-up page *
        return render_template('error.html', message='Username or password cannot be empty.', button="Sign Up Again", url='signup')

    # Case2: check whether data has been entered
    invalid_chars = {"'", '"', ' '}
    if set(username) & invalid_chars or set(password) & invalid_chars:
        # Button should link to sign-up page *
        return render_template('error.html', message='Username or password cannot contain spaces or quote characters.', button="Sign Up Again", url='signup')

    # Case3: check whether username exists
    username_check = db.execute(text(f"SELECT * FROM users WHERE username='{username}'")).fetchall()
    if len(username_check) != 0:
        # Button should link to sign-up page *
        return render_template('error.html', message='Username already exists.', button="Sign Up Again", url='signup')
    
    # Case4: not matched password
    if password != password2:
        # Button should link to sign-in page *
        return render_template('error.html', message="Passwords do not match.", button="Sign Up Again", url='signup')
    
    db.execute(text('INSERT INTO users (username, password) VALUES (:username, :password)'),
                {'username': username, 'password': password})
    db.commit()

    # Store current user
    session["current_user"] = username
    
    return render_template('success.html')


# The search page
@app.route('/search', methods=['POST', 'GET'])
def search():

    # Link to sign-in page if no user is currently signed in
    if session.get('current_user') is None:
        return render_template('main.html')

    # Render the search page if no search has happened yet
    if request.method == 'GET':
        return render_template('search.html', results=None)
    
    # Get the search input
    query = request.form.get('query').lower()

    # Handle special characters in the query to prevent SQL injections
    query = ''.join(c if c.isalnum() or c == ' ' else '_' for c in query)

    # Form and execute the SQL query
    sql_query = f"""
    SELECT * FROM books
    WHERE LOWER(title) LIKE '%{query}%'
    OR LOWER(isbn) LIKE '%{query}%'
    OR LOWER(author) LIKE '%{query}%';
    """
    results = list(db.execute(text(sql_query)))

    # Render the results page (same page, but showing new results)
    return render_template('search.html', results=results)


# The book page
@app.route('//book/<string:isbn>', methods=['GET', 'POST'])
def book(isbn):

    # Link to sign-in page if no user is currently signed in
    if session.get('current_user') is None:
        return render_template('main.html')

    if request.method == 'POST':
        # Check repeated reviews from same user
        check_review = db.execute(text(f"SELECT username FROM reviews WHERE book_isbn = '{isbn}'")).fetchall()
        if check_review != []:
            return render_template('error.html', message='Each user can submit only one review per book. ', button="Go back", url=f'/book/{isbn}')

        # If a post request is sent, add the posted review to the reviews table in the database
        try:
            rating = request.form['rating']
        except:
            return render_template('error.html', message='Rating is required for review sessions.', button="Go back", url=f'/book/{isbn}')
        
        # Get text review and commit to reviews table *Should we allow users to get blank in text review?*
        review = request.form.get('review').strip()
        db.execute(text('INSERT INTO reviews (review, username, book_isbn, rating) VALUES (:review, :user, :isbn, :rating)'),
                {'review': review, 'user': session['current_user'], 'isbn': isbn, 'rating': rating})
        db.commit()

    # Get the book corresponding to the passed in isbn
    book = db.execute(text(f"SELECT * FROM books WHERE isbn = '{isbn}'")).fetchone()
    # Get all current review information for the book
    reviews = db.execute(text(f"SELECT review, username, rating FROM reviews WHERE reviews.book_isbn = '{isbn}'")).fetchall()
    db.commit()

    try:
        # Get info from google book api
        res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": f"isbn:{isbn}"})
        data = res.json()
        average_rating = data["items"][0]["volumeInfo"]["averageRating"]
        reviews_count = data["items"][0]["volumeInfo"]["ratingsCount"]
    except:
        average_rating = "No Rating"
        reviews_count = "No Reviews"

    # Render the book page
    return render_template('book.html', book=book, reviews=reviews,
                        current_user=session.get('current_user'), 
                        average_rating=average_rating,
                        reviews_count=reviews_count)


@app.route('/logout')
def logout():
    # Log the user out and return to to the homepage
    if session.get('current_user') is not None:
        session.pop('current_user')
    return render_template('main.html')

#===========================================================================================
#Lab2

# api
@app.route('/api/book/<string:isbn>', methods=['GET', 'POST'])
def book_api(isbn):
    # Link to sign-in page if no user is currently signed in
    if session.get('current_user') is None:
        return render_template('main.html')
        
    book = db.execute(text(f"SELECT * FROM books WHERE isbn = '{isbn}'")).fetchone()
    if book is None:
        return jsonify({"error": "Invalid isbn number"}),404
    
    """
    # Get average rating and number of reviews from local database
    average_rating = db.execute(text(f"SELECT AVG(rating) FROM reviews WHERE reviews.book_isbn = '{isbn}'")).fetchall()
    reviews_count = db.execute(text(f"SELECT COUNT(rating) FROM reviews WHERE reviews.book_isbn = '{isbn}'")).fetchall()
    """
    try:
        # Get info from google book api
        res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": f"isbn:{isbn}"})
        data = res.json()
        isbn_13 = data["items"][0]["volumeInfo"]["industryIdentifiers"][0][ "identifier"]
        average_rating = data["items"][0]["volumeInfo"]["averageRating"]
        reviews_count = data["items"][0]["volumeInfo"]["ratingsCount"]
    except:
        isbn_13 = "null"
        average_rating = "null"
        reviews_count = "null"

    # Render json
    return jsonify({
        "title": book.title,
        "author": book.author,
        "publishedDate": book.year,
        "ISBN_10": book.isbn,
        "ISBN_13": isbn_13, 
        "reviewCount": reviews_count, 
        "averageRating": average_rating
    })
