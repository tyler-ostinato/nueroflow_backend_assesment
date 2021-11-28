from enum import unique
from os import EX_CONFIG
import re
import bcrypt
from flask import Flask, render_template, url_for, redirect, session, request
from flask_session import Session
import flask_login
from flask_login.utils import login_required
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_manager, login_user, LoginManager, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms import validators
from wtforms.validators import InputRequired, Length, ValidationError
from flask_bcrypt import Bcrypt
import json
import requests


app = Flask(__name__)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'thisisasecretkey'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)


class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_user_name = User.query.filter_by(
            username=username.data).first()
        if existing_user_name:
            raise ValidationError(
                "That username already exists. Please choose a different name.")


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Username"})

    password = PasswordField(validators=[InputRequired(), Length(
        min=4, max=20)], render_kw={"placeholder": "Password"})

    submit = SubmitField("Login")


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        session['username'] = form.username.data
        # check if user in database
        if user:
            # check if password matches hash
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
        
    return render_template('login.html', form=form)

@app.route('/dashboard', methods=['GET','POST'])
@login_required
def dashboard():
    # get the user for this session
    user = session['username']
    # get list of moods for the user dashboard
    response = requests.get(f'http://127.0.0.1:5001/mood?user={user}')
    return render_template('dashboard.html', jsonfile=json.dumps(response.json()))

@app.route('/logout', methods=['GET','POST'])
def logout():
    # log out user and route them to login page
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET','POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
