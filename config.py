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
if __name__ == '__main__':
    DEBUG = True
#USERNAME = 'admin'
#PASSWORD = 'default'
SESSION_COOKIE_NAME = 'learn'

# create our little application :)
app = Flask('learn')
app.config.from_object(__name__)

application = app

# Arrange our file readers
import util
Reader = util.MultiReader([util.DirFileReader(worddir)])
list_wordfiles = Reader.list
get_wordfile = Reader.get
