# Richard Darst, April 2015

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy


from config import app
db = SQLAlchemy(app)

class User(db.Model):
    uid = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120), unique=True)
    def __init__(self, username, email):
        self.username = username
        self.email = email
    def __repr__(self):
        return '<User %r>' % self.username
class UserAttributes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.relationship('User', backref='answers', lazy='dynamic')


class Answer(db.Model):
    aid = db.Column(db.Integer, primary_key=True) # answer ID
    # user ID
    user = db.relationship('User', backref='answers', lazy='dynamic')
    sid = db.Column(db.Integer)                   # session ID
    ts = db.Column(db.DateTime)
    q = db.Column(db.String(256))
    a = db.Column(db.String(256))
    correct = db.Column(db.Boolean)


class Hint(db.Model):
    hid = db.Column(db.Integer, primary_key=True)
    ts = db.Column(db.DateTime)
    text = db.Column(db.String(256))
