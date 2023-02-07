from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class Book(db.Model):
    __tablename__ = 'books'
    isbn = db.Column(db.String, primary_key=True)
    title = db.Column(db.String, nullable=False)
    author= db.Column(db.String, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    review = db.relationship("Review", backref='book', lazy=True)

class User(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String, primary_key=True)
    password = db.Column(db.String, nullable=False)
    review = db.relationship("Review", backref='user', lazy=True)
    
class Review(db.Model):
    __tablename__ = 'reviews'
    id = db.Column(db.Integer, db.Sequence('user_id_seq'), primary_key=True) 
    review = db.Column(db.String, nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String, db.ForeignKey('users.username'))
    book_isbn = db.Column(db.String, db.ForeignKey('books.isbn'))

