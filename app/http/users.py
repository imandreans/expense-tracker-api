from flask import Blueprint, current_app
from flask import render_template, url_for, request, redirect, flash, make_response, current_app
import jwt

from datetime import datetime, timedelta, timezone
from supabase import Client
import os

from flask_wtf import FlaskForm

from wtforms import StringField, SubmitField, FloatField, PasswordField
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
    bcrypt = current_app.bcrypt

    current_app.logger.info("\x1b[38;20mAttemtping to create new account...")
    try:
        if form.validate_on_submit() and request.method == 'POST':
            username = form.username.data

            password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            balance  = form.balance.data
            
            user = conn.table("Users").select("*").eq("username", username).execute()
            if len(user.data) == 0:
                conn.table("Users").insert({"username": username,
                                        "password": password,
                                        "balance": balance}).execute()
                current_app.logger.info("New account created!")
                return redirect(url_for('user.login'))
            
            current_app.logger.warning("Account is already exist!")
            flash('Username already Exist')
    except Exception as e:
        current_app.logger.error(f"\x1b[31;20m{e}")
    return render_template('signup.html', form=form)

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    conn: Client = current_app.supabase
    bcrypt = current_app.bcrypt
    form = LogInForm()
    if form.validate_on_submit() and request.method == 'POST':
        username = form.username.data
        password = form.password.data
        try:
            current_app.logger.info("\x1b[38;20mAttempting to Login...")
            user = conn.table("Users").select("*").eq("username", username).execute()
            check_password = bcrypt.check_password_hash(user.data[0]['password'], password)
            if check_password:
                exp = datetime.now(timezone.utc) + timedelta(days=1)

                current_app.logger.info("Creating token...")
                token = jwt.encode({
                        'user' : user.data[0]['username'],
                        'expiration': int(exp.timestamp())
                }, os.getenv('JWT_SECRET_KEY'))
                response = make_response(redirect(url_for('home')))
                response.set_cookie('auth_token',
                                    token,
                                    httponly=True,
                                    secure=True,
                                    samesite='Strict')
                current_app.logger.info("\x1b[38;20mLogin Successfully!")
                return response
            else:
                flash('username or password isnt valid', 'warning')
        except Exception as e:
                current_app.logger.error(f"\x1b[31;20m{e}")
                flash('username or password isnt valid', 'warning')
            
    return render_template('login.html', form=form)

@user_bp.route('/logout')
def logout():
    try:
        current_app.logger.info("\x1b[38;20mLogging out...")
        response = make_response(redirect(url_for('home')))
        response.set_cookie('auth_token', expires=0)
        current_app.logger.info("\x1b[38;20mLogged out!")
    except Exception as e:
        current_app.logger.error(f"\x1b[31;20m{e}")
    return response


        
