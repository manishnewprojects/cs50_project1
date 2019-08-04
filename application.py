import os

from flask import Flask, session, render_template, request, flash 
from flask import redirect, session, abort, url_for,session,logging,request 
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = os.urandom(12)
app.config['FLASK_DEBUG']=1 
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://ktvjqnlkicstdh:12d3502af6b551ee281300b1a3fe36f6646c953d9eeeaf44b25afde404c29b65@ec2-174-129-41-127.compute-1.amazonaws.com:5432/d1r9eob107ife4'
db = SQLAlchemy(app)

class user(db.Model):
	__tablename__ = "user_info"
	id 		      = db.Column(db.Integer, primary_key=True)
	user_email 	  = db.Column(db.String(120), unique=True)
	username      = db.Column(db.String(80))
	user_password = db.Column(db.String(80))


@app.route("/")
def index():
	if not session.get('logged_in'):
		return render_template("index.html")
	else:
		return redirect(url_for('homepage', username = session.get('username')))



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
			return redirect(url_for('homepage', username = uname))
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


@app.route("/logout")
def logout():
	session['logged_in'] = False
	return index()

@app.route("/homepage/<username>", methods=["GET", "POST"])
def homepage(username):
	return "Hello " +username+ "! Welome Back! Enjoy the site  <a href=\"/logout\">Logout</a>"


if __name__ == "__main__":
	app.run(debug=True,host='0.0.0.0', port=5000)


