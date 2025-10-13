from flask import Blueprint
from flask import render_template, url_for, request, redirect, flash, make_response, current_app
from flask import Flask
from functools import wraps

import jwt

from datetime import datetime, timedelta, timezone
from supabase import create_client, Client
import os
from blueprints.routes.users import user_bp
import os
from supabase import create_client, Client

from flask_bcrypt import Bcrypt

import os
from os.path import join, dirname
from dotenv import load_dotenv



from flask_wtf import CSRFProtect
root_path = os.path.dirname(os.path.abspath(os.path.join(__file__, '..')))
app = Flask(__name__, root_path=root_path, template_folder="templates")
@app.route('/', methods=['GET', 'POST'])
def home():
    token = request.cookies.get('auth_token')
    conn: Client = current_app.supabase
    if token:
        payload = jwt.decode(token, os.getenv('JWT_SECRET_KEY'), algorithms=["HS256"])
        user = conn.table("Users").select("*").eq("username", payload['user']).execute()
        balance = user.data[0]['balance']
        user_id = user.data[0]['id']

        expenses = conn.table("Expenses").select("*").eq('user_id', user_id)

        start_date = request.form['start-date'] if 'start-date' in request.form else ''
        end_date = request.form['end-date'] if 'end-date' in request.form else ''

        if 'filter-date' in request.form:
            selected_filter= request.form['filter-date']
            current_date = datetime.now()
            match selected_filter:
                case 'past-month':
                    past_month = current_date - timedelta(days=30)
                    expenses = expenses.gte("date", past_month)
                case 'past-week':
                    past_week = current_date - timedelta(days=7)
                    expenses = expenses.gte("date", past_week)
                case 'last-three-months':
                    last_three_months = current_date - timedelta(days=90)
                    expenses = expenses.gte("date", last_three_months)

        if len(start_date) > 0:
            expenses = expenses.gte("date", start_date)

        if len(end_date) > 0:
            expenses = expenses.lte("date", end_date)

        selected_date = start_date, end_date
        
        expenses = expenses.execute()
        expenses = expenses.data

        return render_template('home.html', selected_date=selected_date, user=payload['user'], expenses=expenses, balance=balance)
    return render_template('home.html')

def create_app():
    app.secret_key = os.getenv("SECRET_KEY")
    app.register_blueprint(user_bp, url_prefix="/user")

    app.csrf = CSRFProtect(app)
    app.bycrypt = Bcrypt(app)

    dotenv_path = '.env'
    load_dotenv(dotenv_path)

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(url,key)

    app.supabase = supabase

    return app