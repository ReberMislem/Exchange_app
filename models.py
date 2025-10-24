from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='viewer')

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100), default='شركة الصرافة')
    company_logo = db.Column(db.String(200), default='bi-bank2')  # Bootstrap icon class

class Currency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    rate = db.Column(db.Float, nullable=False, default=1.0)
    last_update = db.Column(db.DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    type = db.Column(db.String(10))
    currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'))
    currency = db.relationship('Currency')
    quantity = db.Column(db.Float, nullable=False)
    buy_rate = db.Column(db.Float)
    sell_rate = db.Column(db.Float)
    total_value_local = db.Column(db.Float)
    profit = db.Column(db.Float)
    notes = db.Column(db.String(255))

class Cashbox(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'))
    currency = db.relationship('Currency')
    inflow = db.Column(db.Float, default=0.0)
    outflow = db.Column(db.Float, default=0.0)
    balance_after = db.Column(db.Float, default=0.0)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    category = db.Column(db.String(64), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'))
    currency = db.relationship('Currency')
    notes = db.Column(db.String(255))

class ExchangeDiff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'))
    currency = db.relationship('Currency')
    old_rate = db.Column(db.Float)
    new_rate = db.Column(db.Float)
    difference_value = db.Column(db.Float)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Debt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    person_name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'))
    currency = db.relationship('Currency')
    due_date = db.Column(db.Date)
    notes = db.Column(db.String(255))
    is_paid = db.Column(db.Boolean, default=False)