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


def get_wordfiles():
    wordfiles = tuple((f, f) for f in sorted(
        x for x in os.listdir(worddir)
        if not (x.endswith('~')
                or x.startswith('.')
                or x.startswith('#'))
        ))
    return wordfiles
def wordfile_filename(fname):
    return worddir+fname


class SelectorForm(Form):
    wordlist = SelectField(choices=get_wordfiles())
    #wordlist = forms.MultipleChoiceField(choices=wordfiles)
    from_english = BooleanField(default=True)
    randomize = BooleanField(default=False)
    provide_choices = BooleanField('Provide hints?', default=False)
    segment = SelectField(default=False)
    list_words = BooleanField(default=False)

listrunner_store = { }

@app.route('/', methods=('GET', 'POST'))
def select():
    SelectorForm.wordlist.choices = get_wordfiles()
    form = SelectorForm(request.form)

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
        runner = ask_algs.ListRunner(
            wordlist,
            from_english=form.from_english.data,
            randomize=form.randomize.data,
            segment=(segment_size*int(form.segment.data), segment_size*(int(form.segment.data)+1)-1) if form.segment.data!='all' else 'all',
            provide_choices=form.provide_choices.data,
            )
        listrunner_store[id_] = runner, time.time()
        if form.list_words.data:
            wordpairs = runner.words
            return render_template('select.html', form=form, wordpairs=wordpairs)
        return redirect(url_for('run'))
    return render_template('select.html', form=form)



class RunForm(Form):
    question = HiddenField()
    answer = StringField()

@app.route('/run/', methods=('GET', 'POST'))
def run():
    runner, creation_time = listrunner_store[session['id']]
    diff = None
    lastquestion = None
    newword_data = None

    form = RunForm()
    if form.validate_on_submit():
        question = form.question.data
        lastquestion = question
        answer = form.answer.data
        if u'ignore' in form.data:
            runner.ignore(question)
        diff = runner.answer(question, answer)
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
                           form=form, diff=diff, newword=newword,
                           lastquestion=lastquestion,
                           newword_data=newword_data)


def makediff(s1, s2):
    """Diff two shifts, returning new two-string diff."""
    import difflib
    differ = difflib.SequenceMatcher()
    differ.set_seqs(s1, s2)
    #debug = False
    #if s2 == "Allie//1200/Ruth//1700/Harstrick":
    #    debug = True
    #for op, i1, i2, j1, j2 in reversed(differ.get_opcodes()):
    #if debug: print "start"
    s1new = [ ]
    s2new = [ ]
    previousOp = None
    for op, i1, i2, j1, j2 in differ.get_opcodes():
        #if debug: print "top"
        #if debug: print op, i1, i2, j1, j2, '->'
        #if debug: print s1, s2
        if op == 'equal':
            if i2-i1 < 4 and len(s1new) > 1 and previousOp == "replace":
                s1new[-2] += s1[i1:i2]
                s2new[-2] += s2[j1:j2]
            else:
                s1new.append(Markup(s1[i1:i2]))
                s2new.append(Markup(s2[j1:j2]))
        elif op == 'insert':
            s2new.extend(('<b>', Markup(s2[j1:j2]), '</b>'))
        elif op == "delete":
            s1new.extend(('<strike>', Markup(s1[i1:i2]), '</strike>'))
        elif op == 'replace':
            s1new.extend(('<strike>', Markup(s1[i1:i2]), '</strike>'))
            s2new.extend(('<b>', Markup(s2[j1:j2]), '</b>'))
        previousOp = op
        #if debug: print s1, s2
        #if debug: print "bottom"
    #if debug: print "done"
    return ''.join(s1new), ''.join(s2new)






if __name__ == '__main__':
    app.run()

