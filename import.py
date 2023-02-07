import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import text

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():
    # Create the necessary tables in the database
    create_tables_query = '''
    CREATE TABLE books (
        isbn VARCHAR PRIMARY KEY,
        title VARCHAR NOT NULL,
        author VARCHAR NOT NULL,
        year INT NOT NULL
    );

    CREATE TABLE users (
        username VARCHAR PRIMARY KEY,
        password VARCHAR NOT NULL
    );

    CREATE TABLE reviews (
        id SERIAL PRIMARY KEY,
        review VARCHAR NOT NULL,
        rating INTEGER NOT NULL,
        username VARCHAR REFERENCES users,
        book_isbn VARCHAR REFERENCES books
    );
    '''
    db.execute(text(create_tables_query))
    db.commit()

    # Populate the `books` table with books from `books.csv`
    with open('books.csv', 'r') as f:
        reader = csv.reader(f)
        next(reader)  # Skip header
        for isbn, title, author, year in reader:
            db.execute(text('INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)'),
                {'isbn': isbn, 'title': title, 'author': author, 'year': int(year)})
        db.commit()

if __name__ == '__main__':
    main()