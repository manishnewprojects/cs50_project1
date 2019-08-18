#Manish Vaidya, 2019, CS50w

import os

from flask import Flask, session, render_template, request, flash 
from flask import redirect, session, abort, url_for,session,logging,request 
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_, and_
 
import requests
from flask import json, jsonify

app = Flask(__name__)

#Goodreads API key
app.config['GOODREADS_KEY']	 = '6Ck8APh3scMY0Ix0NDcA'

#Defs to allow session
app.config['SESSION_TYPE']	 = 'filesystem'
app.secret_key 				 = os.urandom(12)
 

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://ktvjqnlkicstdh:12d3502af6b551ee281300b1a3fe36f6646c953d9eeeaf44b25afde404c29b65@ec2-174-129-41-127.compute-1.amazonaws.com:5432/d1r9eob107ife4'
db = SQLAlchemy(app)

#Database models for Users, Books, Reviews
class user(db.Model):
	__tablename__ = "user_info"
	id 		      = db.Column(db.Integer, primary_key=True)
	user_email 	  = db.Column(db.String(120), unique=True)
	username      = db.Column(db.String(80))
	user_password = db.Column(db.String(80))


class book_data(db.Model):
	__tablename__ = "book_info"
	title 		  		= db.Column(db.String(120))
	author 	 	  		= db.Column(db.String(120))
	isbn          		= db.Column(db.String(80), unique=True, primary_key=True)
	year          		= db.Column(db.String(80))
	review_count   		= db.Column(db.Integer)
	number_of_ratings  	= db.Column(db.Numeric(4,2))
	average_rating  	= db.Column(db.Integer)
 
class book_reviews(db.Model):
	__tablename__ = "book_reviews"
	isbn          		= db.Column(db.String(80))
	username          	= db.Column(db.String(80), primary_key=True)
	review 		   		= db.Column(db.String(400))
	 

#Base 
@app.route('/')
def index():
	if not session.get('logged_in'):
		return render_template("index.html")
	else:
		return render_template("search.html", user = session.get('username'))



@app.route('/login', methods=["GET", "POST"])
def login():
	error = "";
	if request.method == "POST":
		uname = request.form["uname"]
		passw = request.form["passw"]

		login = user.query.filter_by(username = uname, user_password = passw).first()
 
		if login is None:
			error = "Login failed. Try agin"
			return render_template("login.html", error_state = error)
		else:
			session['logged_in'] = True
			session['username']  = uname 
			session['first_login'] = True
			return render_template("search.html")

	return render_template("login.html", error_state = error)


@app.route('/register', methods=["GET","POST"])
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


#Search results page
@app.route('/search', methods=["GET","POST"])
def search():

	session['first_login'] = True
	session['user_has_rated'] = False
	session['user_has_reviewed'] = False
	uname = session['username']  


 	if request.method == "POST":
	  	search_term=request.form.get('search_term')
	  	search_string = '';
 	 	
 	 	if search_term:
 	 		search_string = "%{}%".format(search_term)
		
		search_results = book_data.query.filter(or_ (book_data.author.ilike(search_string), book_data.isbn.like(search_string), book_data.title.ilike(search_string)) ).all()
		 

		if not search_results:
			flash('No results found!')
			return render_template("search.html")
		else:
		# display results
			return render_template("search.html", user=uname, search_results=search_results)
	return render_template("search.html")

#API for Book data
@app.route('/api/<isbn>', methods=["GET","POST"])
def vaidyalib_API(isbn):
	if request.method == "GET":
		search_results = book_data.query.filter(book_data.isbn == isbn).first()

		if search_results:
			book_info = {
				"title"  		: search_results.title,
				"author" 		: search_results.author,
				"year"  		: search_results.year,
				"isbn" 			: search_results.isbn,
				"review_count"  : search_results.review_count,
				"average_score" : str(search_results.average_rating)
			}

	 		response = jsonify(book_info)
			response.status_code = 200
			return response
		else:
			response = jsonify("404: Nothing Here")
			response.status_code = 404
			return response

	return render_template("search.html")


#Get book info
@app.route('/book_details/<isbn>', methods=["GET","POST"])
def book_details(isbn):
	if request.method == "GET":
		session['current_book']=isbn

		reviews = book_reviews.query.filter(book_reviews.isbn == isbn).all()

		for reviewed_by_current_user in reviews:
			if (reviewed_by_current_user.username.strip() == session['username'].strip()):
				session['user_has_reviewed'] = True

		goodreads_results = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "6Ck8APh3scMY0Ix0NDcA", "isbns": isbn})

		search_results = book_data.query.filter(book_data.isbn == isbn).first()

		return render_template("book_details.html", book = search_results, goodreads_results = goodreads_results.json(), reviews=reviews )
	return render_template("search.html")



@app.route('/rate_book', methods=["GET","POST"])
def rate_book():
	rvalue = -1
	if request.method == "POST":

		session['user_has_rated'] = True
		session['first_login'] == True

		rating = int(request.form['value'])

		current_rating = book_data.query.filter_by(isbn = session['current_book']).first()

		if current_rating.number_of_ratings is not None:
			ratings 		= current_rating.number_of_ratings
			average_ratings = current_rating.average_rating
			average_ratings = ((average_ratings*ratings)+rating)/(ratings+1)

			current_rating.average_rating 	 = average_ratings
			current_rating.number_of_ratings = ratings+1
		else:
			current_rating.number_of_ratings = 1
			current_rating.average_rating    = rating
		db.session.commit()

		return redirect(url_for('book_details', isbn=session['current_book']))
	return url_for('book_details', isbn=session['current_book'])



@app.route('/review_book', methods=["GET","POST"])
def review_book():

	if request.method == "POST":
		review = request.form['review']
 		current_review = book_data.query.filter_by(isbn = session['current_book']).first()

		if current_review.review_count is not None:
			current_review.review_count = current_review.review_count+1
			db.session.commit()
		else:
			current_review.review_count = 1
			db.session.commit()

		review_data = book_reviews(username = session['username'], isbn = session['current_book'], review = review)
		db.session.add(review_data)
		db.session.commit()
		
		return redirect(url_for('book_details', isbn=session['current_book']))

	return url_for('book_details', isbn=session['current_book'])



@app.route("/logout")
def logout():
	session.pop('username', None)
	session['logged_in'] = False
	return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug = True)

 
