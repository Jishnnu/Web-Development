import os
import csv
from flask import Flask
from flask import render_template,request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app=Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

engine = create_engine(os.getenv("YOUR_POSTGRE_SQL_URI"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
@login_required
def home():
    return render_template("/HTML/BookMain.html")

@pp.route("/HTML/Login.html", methods="["GET", "POST"]")
def Login():
    session.clear()
    Username = request.form.get("username")
    Password = request.form.get("password")
    if not request.form.get("username"):
        return render_template("Error.html", message="Please provide a valid Username")
    elif not request.form.get("password"):
          return render_template("Error.html", message="Incorrect Password")

    ROWS = db.execute("SELECT * FROM USERS WHERE username = :username", {"username":username})
        RESULT = ROWS.fetchone()

    if RESULT == None:
        print("ERROR")

        session["user_id"] = result[0]
        session["user_name"] = result[1]
        return redirect("/")

    else:
        return render_template("Login.html")


@app.route("/HTML/Signup.html")
def Signup():
    session.clear()
    render_template("/HTML/Signup.html")
    Name = request.form.get("Name")
    Email = request.form.get("Email")

    if request.method == "POST":
        if not request.form.get("Email"):
          return render_template("Error.html", message="You must provide an authentic Email Address")
    userCheck = db.execute("SELECT * FROM USERS WHERE Email = :Email",{"Email":request.form.get("Email")}).fetchone()
    if userCheck:
        print("Email already exists. Please Login")

    Username = request.form.get("username")
    if not request.form.get("username"):
        return render_template("Error.html", message="You must provide an authentic Username")

    userCheck = db.execute("SELECT * FROM USERS WHERE username = :username",{"username":request.form.get("username")}).fetchone()
        if userCheck:
            return render_template("Error.html", message="Username already exists. Please Login")

    Password = request.form.get("Password")
    if not request.form.get("password"):
        return render_template("Error.html", message="You must provide an authentic Password")

    db.execute("INSERT INTO USERS (Name, Email, username, password) VALUES (:Name, :Email, :username, :password)",{"Name":request.form.get("Name"), "Email":request.form.get("Email"),"username":request.form.get("username"),"password":request.form.get("Password")})
    db.commit()
    return redirect("/HTML/Login.html")

@app.route("/HTML/Logout.html")
def Logout():
    session.clear()
    return redirect("/")

@app.route("/HTML/Search.html", methods="["GET", "POST"]")
@login_required
def Search():
    if not request.args.get("book"):
         return render_template("Error.html", message="You must provide a book.")

    query = "%" + request.args.get("book") + "%"
    query = query.title()
    ROWS = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn LIKE :query OR \
                        title LIKE :query OR \
                        author LIKE :query LIMIT 15",
                        {"query": query})

     if ROWS.rowcount == 0:
        return render_template("Error.html", message="We can't find books with that description.")
    books = ROWS.fetchall()
    return render_template("Results.html", books=books)

@app.route("/book/<isbn>", methods=["GET","POST"])
@login_required
def book(isbn):

    if request.method == "POST":
        currentUser = session["user_id"]
        rating = request.form.get("rating")
        comment = request.form.get("comment")

        ROW = db.execute("SELECT id FROM books WHERE isbn = :isbn",
                        {"isbn": isbn})

        bookId = ROW.fetchone()
        bookId = bookId[0]

        # Check for user submission (ONLY 1 review/user allowed per book)
        row2 = db.execute("SELECT * FROM reviews WHERE user_id = :userid AND bookid = :bookid",
                    {"userid": currentUser,
                     "bookid": bookId})

        # A review already exists
        if row2.rowcount == 1:
            flash('You already submitted a review for this book', 'warning')
            return redirect("/book/" + isbn)

        rating = int(rating)

        db.execute("INSERT INTO reviews (userid, bookid, comment, rating) VALUES \
                    (:userid, :bookid, :comment, :rating)",
                    {"userid": currentUser,
                    "bookid": bookId,
                    "comment": comment,
                    "rating": rating})
        db.commit()
        return redirect("/book/" + isbn)

     else:
        ROW = db.execute("SELECT isbn, title, author, year FROM books WHERE \
                        isbn = :isbn",
                        {"isbn": isbn})

        bookInfo = ROW.fetchall()

    key = os.getenv("cIgWyhuIAssjSqVmJyDubQ")
    query = requests.get("https://www.goodreads.com/book/review_counts.json",params={"key": key, "isbns": isbn})
        response = query.json()
        response = response['books'][0]
        bookInfo.append(response)

ROW = db.execute("SELECT id FROM books WHERE isbn = :isbn",
                        {"isbn": isbn})

        book = ROW.fetchone()
        book = book[0]

        results = db.execute("SELECT users.username, comment, rating, \
                            to_char(time, 'DD Mon YY - HH24:MI:SS') as time \
                            FROM users \
                            INNER JOIN reviews \
                            ON users.id = reviews.userid \
                            WHERE bookid = :book \
                            ORDER BY time",
                            {"book": book})
        reviews = results.fetchall()
        return render_template("Book.html", bookInfo=bookInfo, reviews=reviews)

@app.route("/api/<isbn>", methods=['GET'])
@login_required
def api_call(isbn):
    row = db.execute("SELECT title, author, year, isbn, \
                    COUNT(reviews.id) as review_count, \
                    AVG(reviews.rating) as average_score \
                    FROM books \
                    INNER JOIN reviews \
                    ON books.id = reviews.bookid \
                    WHERE isbn = :isbn \
                    GROUP BY title, author, year, isbn",
                    {"isbn": isbn})

    if row.rowcount != 1:
        return jsonify({"Error": "Invalid book ISBN"}), 422

    tmp = ROW.fetchone()
    result = dict(tmp.items())

    result['average_score'] = float('%.2f'%(result['average_score']))
    return jsonify(result)
