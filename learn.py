# -*- coding: utf-8 -*-

# all the imports
import os
import random
import re
import sqlite3
import time

import sys
sys.path.append(os.path.dirname(__file__))
sys.path.append('/srv/learn/pymod/')

from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from flask import Markup # html escaping

from wtforms import Form, BooleanField, TextField, PasswordField, \
     StringField, SelectField, HiddenField, validators
from flask_wtf import Form

import ask_algs
import util

# configuration
worddir = '/srv/learn/data/'
#DATABASE = '/tmp/flaskr.db'
secret_fname = os.path.join(os.path.dirname(__file__), 'secret.txt')
SECRET_KEY = open(secret_fname).read()
#if os.path.exists(os.path)
#SECRET_KEY = 'tnaou64oatn!#%>ntao64\ue7!$%$%@!ouiuueau'
if __name__ == '__main__':
    DEBUG = True
#USERNAME = 'admin'
#PASSWORD = 'default'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

application = app



class SelectorForm(Form):
    wordlist = SelectField(choices=util.get_wordfiles())
    #wordlist = forms.MultipleChoiceField(choices=wordfiles)
    from_english = BooleanField(default=True)
    randomize = BooleanField(default=False)
    provide_choices = BooleanField('Provide hints?', default=False)
    segment = SelectField(default=False)
    alg = SelectField("Memorization algorithm")
    do_list_words = BooleanField(default=False)

listrunner_store = { }

@app.route('/', methods=('GET', 'POST'))
def select():
    SelectorForm.wordlist.choices = util.get_wordfiles()
    form = SelectorForm(request.form)
    form.alg.choices = [(name, name) for name in ask_algs.list_algs()]

    # Compute options for segments (0-24, 25-30, etc)
    choices = [('all', 'All'), ]
    segment_size = 20
    for i in range(200//segment_size):
        choices.append((str(i), '% 3d-% 3d'%(segment_size*i, segment_size*(i+1)-1)))
    form.segment.choices = choices

    if form.validate_on_submit():
        wordlist = form.wordlist.data
        session['wordlist'] = wordlist
        id_ = random.randint(0, 2**32-1)
        session['id'] = id_
        run_class = ask_algs.get_alg(form.alg.data)
        runner = run_class(
            wordlist,
            from_english=form.from_english.data,
            randomize=form.randomize.data,
            segment=(segment_size*int(form.segment.data), segment_size*(int(form.segment.data)+1)-1) if form.segment.data!='all' else 'all',
            provide_choices=form.provide_choices.data,
            )
        if form.do_list_words.data:
            wordpairs = runner.words
            return render_template('select.html', form=form, wordpairs=wordpairs)
        listrunner_store[id_] = runner, time.time()
        return redirect(url_for('run'))
    return render_template('select.html', form=form)



class RunForm(Form):
    question = HiddenField()
    answer = StringField()

@app.route('/run/', methods=('GET', 'POST'))
def run():
    runner, creation_time = listrunner_store[session['id']]
    results = dict(correct=True)
    lastquestion = None
    newword_data = None

    form = RunForm()
    if form.validate_on_submit():
        question = form.question.data
        lastquestion = question
        answer = form.answer.data
        if u'ignore' in form.data:
            runner.ignore(question)
        results = runner.answer(question, answer)
    else:
        pass
    newword, newword_data = runner.question()
    if newword == StopIteration:
        # Have some handling of the end of process...
        return redirect(url_for('select'))
    form = RunForm(formdata=None,
                   data=dict(question=newword, answer=None))

    session.modified = True
    return render_template('run.html',
                           form=form, results=results, newword=newword,
                           lastquestion=lastquestion,
                           newword_data=newword_data)



if __name__ == '__main__':
    app.run()

