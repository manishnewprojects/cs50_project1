import os

from flask import Flask, session, render_template, request, flash 
from flask import redirect, session, abort, url_for,session,logging,request 
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_

import requests

app = Flask(__name__)
app.config['GOODREADS_KEY'] = '6Ck8APh3scMY0Ix0NDcA'
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = os.urandom(12)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://ktvjqnlkicstdh:12d3502af6b551ee281300b1a3fe36f6646c953d9eeeaf44b25afde404c29b65@ec2-174-129-41-127.compute-1.amazonaws.com:5432/d1r9eob107ife4'
db = SQLAlchemy(app)

class user(db.Model):
	__tablename__ = "user_info"
	id 		      = db.Column(db.Integer, primary_key=True)
	user_email 	  = db.Column(db.String(120), unique=True)
	username      = db.Column(db.String(80))
	user_password = db.Column(db.String(80))


class book_data(db.Model):
	__tablename__ = "book_info"
	title 		  = db.Column(db.String(120))
	author 	 	  = db.Column(db.String(120))
	isbn          = db.Column(db.String(80), unique=True, primary_key=True)
	year          = db.Column(db.String(80))
	review_count  = db.Column(db.Integer)
	average_score = db.Column(db.Integer)


@app.route("/")
def index():
	if not session.get('logged_in'):
		return render_template("index.html")
	else:
		return render_template("homepage.html", user = session.get('username'))



@app.route('/login', methods=["GET", "POST"])
def login():
	if request.method == "POST":
		uname = request.form["uname"]
		passw = request.form["passw"]

		login = user.query.filter_by(username = uname, user_password = passw).first()
 
		if login is None:
			return redirect(url_for("index"))
		else:
			session['logged_in'] = True
			session['username']  = uname 
			return render_template("homepage.html", user = uname)
	return render_template("login.html")


@app.route("/register", methods=["GET","POST"])
def register():
	if request.method == "POST":
		uname = request.form['uname']
		mail  = request.form['mail']
		passw = request.form['passw']

		duplicate = user.query.filter_by(username = uname).first()

		if duplicate is None:
			register = user(username = uname, user_email = mail, user_password = passw)
			db.session.add(register)
			db.session.commit()
			return redirect(url_for("login"))
		else:
			error = 'Username already taken. Please try again!'
			return render_template("register.html", error = error)

	error = ''
	return render_template("register.html", error = error)



@app.route('/search', methods=["GET","POST"])
def search():
 	if request.method == "POST":
	  	search_term=request.form.get('search_term')
 	 	
 	 	search_string = "%{}%".format(search_term)
		search_results = book_data.query.filter(or_ (book_data.author.ilike(search_string), book_data.isbn.like(search_string), book_data.title.ilike(search_string)) ).all()
		 

		if not search_results:
			flash('No results found!')
			return render_template("search.html")
		else:
		# display results
			return render_template("search.html", search_results=search_results)

	return render_template("search.html")

@app.route('/api/<isbn>', methods=["GET","POST"])
def api(isbn):
	print("got ISBN",isbn)
	goodreads_results = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "6Ck8APh3scMY0Ix0NDcA", "isbns": isbn})
	print(goodreads_results.json())

	return render_template("search.html")


@app.route("/logout")
def logout():
	session['logged_in'] = False
	return index()

 
 
