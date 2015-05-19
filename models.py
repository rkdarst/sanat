# Richard Darst, April 2015

import datetime

from flask import Flask
#from flask.ext.sqlalchemy import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_user import login_required, UserManager, UserMixin, SQLAlchemyAdapter


from config import app
db = SQLAlchemy(app)
mail = Mail(app)                                # Initialize Flask-Mail

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    uid = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False, server_default='')
    reset_password_token = db.Column(db.String(100), nullable=False, server_default='')

    # User email information
    email = db.Column(db.String(255), nullable=False, unique=True)
    confirmed_at = db.Column(db.DateTime())

    # User information
    active = db.Column('is_active', db.Boolean(), nullable=False, server_default='0')
    first_name = db.Column(db.String(100), nullable=False, server_default='')
    last_name = db.Column(db.String(100), nullable=False, server_default='')

    roles = db.relationship('Role', secondary='user_roles',
                            backref=db.backref('users', lazy='dynamic'))

    def __repr__(self):
        return '<User %r>' % self.username
    def get_id(self):
        return self.uid

# Define the Role DataModel
class Role(db.Model):
    __tablename__ = 'role'
    role_id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)

# Define the UserRoles DataModel
class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    id = db.Column(db.Integer(), primary_key=True)
    uid = db.Column(db.Integer(), db.ForeignKey('user.uid', ondelete='CASCADE'))
    role_id = db.Column(db.Integer(), db.ForeignKey('role.role_id', ondelete='CASCADE'))

class UserAttributes(db.Model):
    __tablename__ = 'user_attributes'
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.Integer, db.ForeignKey('user.uid'))
    #uid = db.relationship(User, backref='answers', lazy='dynamic')


class Answer(db.Model):
    __tablename__ = 'answer'
    aid = db.Column(db.Integer, primary_key=True) # answer ID
    # user ID
    uid = db.Column(db.Integer, db.ForeignKey('user.uid'))
    #uid = db.relationship(User, backref='answers', lazy='dynamic')
    sid = db.Column(db.Integer)                   # session ID
    lid = db.Column(db.Integer)                   # list ID
    ts = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    q = db.Column(db.String(256))
    a = db.Column(db.String(256))
    c = db.Column(db.String(256))
    correct = db.Column(db.Float)


class Hint(db.Model):
    __tablename__ = 'hint'
    hid = db.Column(db.Integer, primary_key=True)
    ts = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    uid = db.Column(db.Integer, db.ForeignKey('user.uid'))
    #uid = db.relationship(User, backref='answers', lazy='dynamic')
    lid = db.Column(db.Integer)                   # list ID
    q = db.Column(db.String(256))
    hint = db.Column(db.String(256))

db.create_all()
db_adapter = SQLAlchemyAdapter(db, User)        # Register the User model
user_manager = UserManager(db_adapter, app)     # Initialize Flask-User
