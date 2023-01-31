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
    return "Project 1: TODO"


# The search page
@app.route('/search', methods=['POST', 'GET'])
def search():

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
@app.route('/book/<string:isbn>')
def book(isbn):

    # Get the book corresponding to the isbn
    book = db.execute(text(f"SELECT * FROM books WHERE isbn = '{isbn}'")).fetchone()

    # Render the book page
    return render_template('book.html', book=book)