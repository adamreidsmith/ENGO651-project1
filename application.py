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


@app.route("/")
def index():
    return render_template("main.html")


@app.route("/signin", methods=["GET"])
def sign_in():
    return render_template("sign_in.html")


@app.route("/signup", methods=["GET"])
def sign_up():
    return render_template("sign_up.html")


@app.route("/login", methods=["POST"])
def log_in():
    #get text from input
    username = request.form.get("username")
    password = request.form.get("password")
    password2 = request.form.get("password2")

    #case1: check whether username exists
    username_check = db.execute(text(f"SELECT * FROM users WHERE username='{username}'")).fetchall()

    if len(username_check) == 0:
        #button should link to sign-up page *
        return render_template('error.html', message= "No this user.", button="Sign Up", url='signup')
    
    #case2: wrong password
    password_check = db.execute(text(f"SELECT * FROM users WHERE username='{username}' AND password='{password}'")).fetchall()
    if len(password_check) == 0:
        #button should link to sign-in page *
        return render_template('error.html', message="Wrong Password.", button="Sign In Again", url='signin')

    #store current user
    if request.method=="POST":
        session["current_user"] = username
    
    return render_template('success.html')


@app.route("/login_new", methods=["POST"])
def log_in_new():
    #get text from input
    username = request.form.get("username")
    password = request.form.get("password")
    password2 = request.form.get("password2")

    #case1: check whether username exists
    username_check = db.execute(text(f"SELECT * FROM users WHERE username='{username}'")).fetchall()
    if len(username_check) != 0:
        #button should link to sign-up page *
        return render_template('error.html', message= 'Repeated username.', button="Sign Up Again", url='signup')
    
    #case2: not matched password
    if password != password2:
        #button should link to sign-in page *
        return render_template('error.html', message="Password are not matched.", button="Sign Up Again", url='signup')
    
    db.execute(text('INSERT INTO users (username, password) VALUES (:username, :password)'),
                {'username': username, 'password': password})
    db.commit()

    #store current user
    if request.method=="POST":
        session["current_user"] = username
    
    return render_template('success.html')


# The search page
@app.route('/search', methods=['POST', 'GET'])
def search():

    if session.get('current_user') is None:
        return render_template('main.html')

    if request.method == 'GET':
        return render_template('search.html', results=None)
    
    # Get the search input
    query = request.form.get('query').lower()

    # Modify the query to handle special characters (replace them with any character)
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

    if session.get('current_user') is None:
        return render_template('main.html')

    if request.method == 'POST':
        # If a post request is sent, add the posted review to the reviews table in the database
        review = request.form.get('review')
        if review != '':
            db.execute(text('INSERT INTO reviews (review, username, book_isbn) VALUES (:review, :user, :isbn)'),
                {'review': review, 'user': session['current_user'], 'isbn': isbn})

    # Get the book corresponding to the isbn
    book = db.execute(text(f"SELECT * FROM books WHERE isbn = '{isbn}';")).fetchone()

    # Get all current review information for the book
    reviews = db.execute(text(f"SELECT review, username FROM reviews WHERE reviews.book_isbn = '{isbn}';")).fetchall()

    # Render the book page
    return render_template('book.html', book=book, reviews=reviews)


@app.route('/logout')
def logout():
    session.pop('current_user')
    return render_template('main.html')