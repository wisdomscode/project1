from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
  __tablename__ = 'user'
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(20), unique=True, nullable=False)
  email = db.Column(db.String(120), unique=True, nullable=False)
  password = db.Column(db.String(60), nullable=False)

  def __init__(self, username, email, password):
    self.username = username
    self.email = email
    self.password = password


class Books(db.Model):
  __tablename__ = 'books'
  id = db.Column(db.Integer, primary_key=True)
  isbn = db.Column(db.String(255), nullable=False)
  title = db.Column(db.String(12), nullable=False)
  author = db.Column(db.String(50), nullable=False)
  year = db.Column(db.String(10), nullable=False)

  def __init__(self, isbn, title, author, year):
    self.isbn = isbn
    self.title = title
    self.author = author
    self.year = year

