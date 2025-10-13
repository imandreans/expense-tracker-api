from flask import Blueprint
from flask import render_template, url_for, request, redirect, flash, make_response, current_app
from functools import wraps
import jwt

from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
import os

from flask_wtf import FlaskForm

from wtforms import StringField, SubmitField, DateField, FloatField, PasswordField, SelectField
from wtforms.validators import DataRequired
from wtforms.widgets import NumberInput

user_bp = Blueprint('user', __name__, template_folder="templates")



class SignUpForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(message='Username is required as your identity')]) 
    balance = FloatField('Balance', default=0, widget=NumberInput(min=0),validators=[DataRequired(message='Balance is required')])
    password = PasswordField('Password', validators=[DataRequired(message='Password is required')])
    submit = SubmitField('Sign Up')

class LogInForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(message='Username is required as your identity')])
    password = PasswordField('Password', validators=[DataRequired(message='Password is required')])
    submit = SubmitField('Log In')



@user_bp.route('/signup', methods=['POST', 'GET'])
def signup():
    form = SignUpForm()
    conn: Client = current_app.supabase
    bycrypt = current_app.bycrypt
    if form.validate_on_submit() and request.method == 'POST':
        username = form.username.data

        password = bycrypt.generate_password_hash(form.password.data).decode('utf-8')
        balance  = form.balance.data
        
        user = conn.table("Users").select("*").eq("username", username).execute()

        if len(user.data) == 0:
            conn.table("Users").insert({"username": username,
                                       "password": password,
                                       "balance": balance}).execute()

            return redirect(url_for('login'))
        
        flash('Username already Exist')

    return render_template('signup.html', form=form)

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    conn: Client = current_app.supabase
    bycrypt = current_app.bycrypt
    form = LogInForm()
    if form.validate_on_submit() and request.method == 'POST':
        username = form.username.data
        password = form.password.data
        
        user = conn.table("Users").select("*").eq("username", username).execute()
        check_password = bycrypt.check_password_hash(user.data[0]['password'], password)
        
        if user and check_password:
            try:
                exp = datetime.now(timezone.utc) + timedelta(days=1)
                token = jwt.encode({
                        'user' : user.data[0]['username'],
                        'expiration': int(exp.timestamp())
                }, os.getenv('JWT_SECRET_KEY'))
                flash("Log In Success!", "info")
                response = make_response(redirect(url_for('home')))
                response.set_cookie('auth_token',
                                    token,
                                    httponly=True,
                                    secure=True,
                                    samesite='Strict')
                return response
            except Exception as e:
                return render_template('400.html', error=e)
        else:
            flash('username or password isnt valid', 'info')
    return render_template('login.html', form=form)

@user_bp.route('/logout')
def logout():
    response = make_response(redirect(url_for('home')))
    response.set_cookie('auth_token', expires=0)
    return response