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
     StringField, SelectField, SelectMultipleField, HiddenField, \
     validators
from flask_wtf import Form

import ask_algs
import util

from config import app, application, worddir


class SelectorForm(Form):
    wordlist = SelectField(choices=util.get_wordfiles())
    #wordlist = forms.MultipleChoiceField(choices=wordfiles)
    from_english = BooleanField(default=True)
    randomize = BooleanField("Randomize fully", default=False)
    randomize_local = BooleanField("Randomize locally", default=False)
    provide_choices = BooleanField('Provide hints?', default=False)
    #segment = SelectField(default=False)
    segment = SelectMultipleField(choices=[('all', 'All'), ], default=['all'])
    alg = SelectField("Memorization algorithm")
    do_list_words = BooleanField(default=False)

listrunner_store = { }

@app.route('/', methods=('GET', 'POST'))
def select():
    SelectorForm.wordlist.choices = util.get_wordfiles()
    # Set default wordlist to the last wordlist used
    form = SelectorForm(request.form,
                        **session.get('last_data', {})   # defaults
                        )
    form.alg.choices = [(name, name) for name in ask_algs.list_algs()]

    # Compute options for segments (0-24, 25-30, etc)
    choices = [('all', 'All'), ]
    segment_size = 20
    for i in range(200//segment_size):
        choices.append((str(i), '% 3d-% 3d'%(segment_size*i, segment_size*(i+1)-1)))
    form.segment.choices = choices

    if form.validate_on_submit():
        wordlist = form.wordlist.data
        # store defaults so that we can pre-seed the form next time
        session['wordlist'] = wordlist
        session['last_data'] = form.data
        id_ = random.randint(0, 2**32-1)
        session['id'] = id_
        run_class = ask_algs.get_alg(form.alg.data)
        randomize = 0
        if form.randomize_local.data:
            randomize = 2
        elif form.randomize.data:
            randomize = 1
        # segment
        segment = 'all'
        if isinstance(form.segment.data, list) and form.segment.data[0] != 'all':
            # multi-select form
            segment = [ ]
            for seg in form.segment.data:
                seg = int(seg)
                segment.append((segment_size*seg, segment_size*(seg+1)-1))
        elif form.segment.data[0] != 'all':
            # single-select form
            seg = int(form.segment.data)
            segment = (segment_size*seg, segment_size*(seg+1)-1)
        print segment
        runner = run_class(
            wordlist,
            from_english=form.from_english.data,
            randomize=randomize,
            segment=segment,
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

