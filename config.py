# Richard Darst, April 2015

import os

from flask import Flask


# configuration
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
worddir = os.path.join(base_dir, 'data')
#DATABASE = '/tmp/flaskr.db'
secret_fname = os.path.join(os.path.dirname(__file__), 'secret.txt')
SECRET_KEY = open(secret_fname).read()
#if os.path.exists(os.path)
#SECRET_KEY = 'tnaou64oatn!#%>ntao64\ue7!$%$%@!ouiuueau'
import __main__
if getattr(__main__, '__file__', None) == "run.py": #__name__ == '__main__':
    DEBUG = True
#USERNAME = 'admin'
#PASSWORD = 'default'
SESSION_COOKIE_NAME = 'learn'

SQLALCHEMY_DATABASE_URI = 'sqlite:///db/learn1.sqlite'
USER_APP_NAME        = "Learn"                # Used by email templates

# Mail info, for flask-user
#MAIL_USERNAME = 'rkd@zgib.net'
#MAIL_PASSWORD = ''
MAIL_DEFAULT_SENDER = 'learn <rkd+learn@zgib.net>'
#MAIL_SERVER = 'localhost'
#MAIL_PORT = 465
#MAIL_USE_SSL = True
#MAIL_USE_TLS = False
#USER_ENABLE_EMAIL = False



# create our little application :)
app = Flask('learn')
app.config.from_object(__name__)

application = app

ADMINS = ['rkd@zgib.net']
if not app.debug:
    import logging
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler('127.0.0.1',
                               'rkd@zgib.net',
                               ADMINS, 'Exception: learn')
    mail_handler.setLevel(logging.ERROR)
    app.logger.addHandler(mail_handler)


# Arrange our file readers
import util
Reader = util.MultiReader([util.DirFileReader(worddir)])
list_wordfiles = Reader.list
get_wordfile = Reader.get
