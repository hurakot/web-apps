import random
import sqlite3
from flask import Flask, Blueprint, g, render_template, request, session, redirect, url_for, flash, get_flashed_messages
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from faker import Faker
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from functools import wraps
from app import db
from app import visit_logs
from app import Users

visitor = Blueprint('visitor', __name__, template_folder='templates', static_folder='static')

DATABASE = "lab5.db"

#Функция подключения БД во время запроса.
def get_db():
	if "db" not in g: #Если БД не подключена во время запроса, то происходит её подключение.
		g.db = db
	return g.db

@visitor.before_request
def before_request():
    g.db = get_db()
	
@visitor.teardown_request
def teardown_request(exception):
	db = g.pop("db", None)
	if db is not None:
		db.close()


@visitor.route("/anarchia")
def index():
	
	result = visit_logs.query.all()
	return "result"

