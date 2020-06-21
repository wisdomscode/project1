import os
import requests

from flask import Flask, session, redirect, render_template, request, url_for, flash, logging, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from passlib.hash import sha256_crypt

import functools

app = Flask(__name__)


# Check for environment variable
if not os.getenv("postgres://piyntukkmhwvge:97c0c359db585f288fe8b42df1e16dbe15f58886c833ce031a3b3f1424f74e9a@ec2-18-233-32-61.compute-1.amazonaws.com:5432/d4s9lk5tgrveda"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


# Set up database

engine = create_engine(os.getenv("postgres://piyntukkmhwvge:97c0c359db585f288fe8b42df1e16dbe15f58886c833ce031a3b3f1424f74e9a@ec2-18-233-32-61.compute-1.amazonaws.com:5432/d4s9lk5tgrveda"))
db = scoped_session(sessionmaker(bind=engine))



# converts tuple to string 
def convertTuple(tup): 
    str =  ''.join(tup) 
    return str


# Average score
def average_score(book_id):
  scores = db.execute("SELECT rate FROM reviews WHERE book_id=:book_id",{"book_id":book_id}).fetchall()
  l_scores = [sum(tup) for tup in scores]
  t_score = sum(l_scores)
  count = len(scores)
  if count == 0:
    avg_score = 0
    count = 0
    return [avg_score, count]
  else:
    average = t_score / count
    avg_score = round(average, 2)
    return [avg_score, count]
  # print(t_score, count, avg_score)

      

@app.route("/")
@app.route("/home")
def home():
  return render_template('home.html')


@app.route("/register", methods=['GET', 'POST'])
def register():
  if request.method == 'POST':
    username = request.form.get("name")
    email = request.form.get("email")
    password = request.form.get("password")
    confirm_pass = request.form.get("confirm_password")
    secure_password = sha256_crypt.encrypt(str(password))
    
    if password == confirm_pass:
      user = db.execute("SELECT * FROM users WHERE name = :name", {"name": username}).fetchone()
      if user:
        flash('That username is taken. Choose a different one', 'danger')
        return redirect(url_for('register'))
      else:
        user_email = db.execute("SELECT * FROM users WHERE email = :email", {"email": email}).fetchone()
        if user_email:
          flash('That email has been registered. Choose a different one', 'danger')
          return redirect(url_for('register'))
        else:
          db.execute("INSERT INTO users (name, email, password) VALUES (:name, :email, :password)",
          {"name": username, "email": email, "password": secure_password})
          db.commit()
          flash('Your Account has been created, you can now log in. ', 'success')
          return redirect(url_for('login'))
    else:
      flash("password does not match", "danger")
      return render_template("register.html")
  return render_template("register.html", title='Register')


@app.route("/login", methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    email = request.form.get("email")
    passwd = request.form.get("password")
    
    user_email_data = db.execute("SELECT email FROM users WHERE email=:email", {"email": email}).fetchone()
    passwordata = db.execute("SELECT password FROM users WHERE email=:email", {"email":email}).fetchone()
    user_name = db.execute("SELECT name FROM users WHERE email=:email", {"email": email}).fetchone()

    if user_email_data is None:
      flash('You are not registered. Please register to continue.', 'danger')
      return redirect(url_for('login'))
    else:
      for pass_data in passwordata:
        if sha256_crypt.verify(passwd, pass_data):
          tuple = (user_name) 
          username = convertTuple(tuple)
          session["username"] = username
          flash('You have been logged in successfully', 'success')
          return redirect(url_for('books'))
        else:
          flash('Login denied. Please check username and password', 'danger')
          return redirect(url_for('login'))
  return render_template("login.html", title='Login')


@app.route("/logout")
def logout():
  session.pop('username', None)
  flash("You are logged out", "success")
  return redirect(url_for("login"))


@app.route("/books", methods=['GET', 'POST'])
def books():
  if 'username' in session:
    username = session['username']
    books = db.execute("SELECT * FROM books").fetchall()
    return render_template('books.html', title='Books', books=books)
  return redirect(url_for("login"))



@app.route("/search", methods=['GET', 'POST'])
def search():
  if 'username' in session:
    username = session['username']
    if request.method == 'POST':
      search_data = request.form.get("search")
      get_result = db.execute("SELECT * FROM books WHERE isbn=:isbn OR title=:title OR author=:author",
                              {"isbn":search_data, "title":search_data, "author":search_data}).fetchall()
      if get_result:
        return render_template('search.html', get_result=get_result)
      else:
        flash('Sorry, we do not have the book you are looking for', 'danger')
        return redirect(url_for('books'))
    return render_template('search.html')
  return redirect(url_for("login"))


@app.route("/books/<int:book_id>")
def book_page(book_id):
  if 'username' in session:
    username = session['username']

    book = db.execute("SELECT * FROM books WHERE book_id=:book_id",{"book_id":book_id}).fetchone()
    reviews = db.execute("SELECT rate, comment, name FROM users JOIN reviews ON reviews.user_id = users.id WHERE book_id=:book_id", {"book_id":book_id}).fetchall()
    book_isbn = db.execute("SELECT isbn FROM books WHERE book_id=:book_id",{"book_id":book_id}).fetchone()

    tuple = (book_isbn)
    isbn = convertTuple(tuple)
    # print(isbn)

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "SngIjzVcck6l56saTAAyw", "isbns": isbn})
    if res.status_code != 200:
      return render_template("book_page.html", title='Book Page', book=book, reviews=reviews)
    data = res.json()

    result = average_score(book_id)
      
    return render_template("book_page.html", title='Book Page', book=book, reviews=reviews, data=data, result=result)



@app.route("/books/<int:book_id>",  methods=['GET', 'POST'])
def review(book_id):
  if request.method == 'POST':
    if 'username' in session:
      username = session['username']

      rate = int(request.form.get("rate"))
      comment = request.form.get("comment")
      u_id = db.execute("SELECT id FROM users WHERE name=:name", {"name":username}).fetchone()
      user_id = functools.reduce(lambda sub, ele: sub * 10 + ele, u_id) 
      # print(username, user_id)

      check_user = db.execute("SELECT * FROM reviews WHERE book_id=:book_id AND user_id=:user_id", {"book_id":book_id, "user_id":user_id}).fetchall()
      if len(check_user) == 0:
        db.execute("INSERT INTO reviews (rate, comment, user_id, book_id) VALUES (:rate, :comment, :user_id, :book_id)",
                          {"rate": rate, "comment": comment, "user_id": user_id, "book_id": book_id})
        db.commit()
        flash('Thank you for rating this book', 'success')
        redirect(url_for('books'))
      else:
        flash('Sorry, you have reviewed this book', 'danger')
        redirect(url_for('books'))
  return redirect(url_for('books'))



@app.route("/api/books/<string:isbn>")
def book_api(isbn):
  if request.method == "GET":
    book = db.execute("SELECT * FROM books WHERE isbn=:isbn", {"isbn":isbn}).fetchone()
    if book is None:
      return jsonify({"error": "Invalid isbn"}), 404
      
    result = average_score(book.book_id)
    return jsonify(
      {
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": book.isbn,
        "review_count": result[1],
        "average_score": result[0]
      })
    return render_template("home.html", jsonify=jsonify)


if __name__ == "__main__":
  app.secret_key="ff28069e9f542ee8a173bda8af2625cf"
  app.run(debug=True)
  
