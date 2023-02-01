import os

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

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
    # if request.method == "POST":
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
    if len(set(username) & invalid_chars) > 0 or len(set(password) & invalid_chars):
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
    # if request.method=="POST":
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
@app.route('/book/<string:isbn>', methods=['GET', 'POST'])
def book(isbn):

    # Link to sign-in page if no user is currently signed in
    if session.get('current_user') is None:
        return render_template('main.html')

    if request.method == 'POST':
        # If a post request is sent, add the posted review to the reviews table in the database
        review = request.form.get('review').strip()
        if review != '':
            db.execute(text('INSERT INTO reviews (review, username, book_isbn) VALUES (:review, :user, :isbn)'),
                {'review': review, 'user': session['current_user'], 'isbn': isbn})
        db.commit()

    # Get the book corresponding to the passed in isbn
    book = db.execute(text(f"SELECT * FROM books WHERE isbn = '{isbn}';")).fetchone()
    # Get all current review information for the book
    reviews = db.execute(text(f"SELECT review, username FROM reviews WHERE reviews.book_isbn = '{isbn}';")).fetchall()
    db.commit()

    # Render the book page
    return render_template('book.html', book=book, reviews=reviews)


@app.route('/logout')
def logout():
    # Log the user out and return to to the homepage
    if session.get('current_user') is not None:
        session.pop('current_user')
    return render_template('main.html')