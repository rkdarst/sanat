# -*- coding: utf-8 -*-

# all the imports
import os
import random
import re
import sqlite3
import time

import sys
sys.path.append(os.path.dirname(__file__))
#sys.path.append('/srv/learn/pymod/')
sys.path.append('/mnt/data1/srv/learn/venv/lib/python2.7/site-packages/')


import flask
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash
from flask import Markup # html escaping
from flask_user import login_required, UserManager, UserMixin, SQLAlchemyAdapter
from flask.ext.login import current_user #.get_id()

from wtforms import Form, BooleanField, TextField, PasswordField, \
     StringField, SelectField, SelectMultipleField, HiddenField, \
     validators
from flask_wtf import Form

import ask_algs

from config import app, application, worddir
import config
import models


class SelectorForm(Form):
    wordlist = SelectField(choices=config.list_wordfiles())
    #wordlist = forms.MultipleChoiceField(choices=wordfiles)
    from_english = BooleanField(default=True)
    randomize = BooleanField("Randomize fully", default=False)
    randomize_local = BooleanField("Randomize locally", default=False)
    provide_choices = BooleanField('Provide hints?', default=False)
    #segment = SelectField(default=False)
    segment = SelectMultipleField(choices=[('all', 'All'), ], default=['all'])
    alg = SelectField("Memorization algorithm")
    do_list_words = BooleanField(default=False)
    do_stats = BooleanField(default=False)

listrunner_store = { }

@app.route('/', methods=('GET', 'POST'))
def select():
    SelectorForm.wordlist.choices = config.list_wordfiles()
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
                segment.append((segment_size*seg, segment_size*(seg+1)))
        elif form.segment.data[0] != 'all':
            # single-select form
            seg = int(form.segment.data)
            segment = (segment_size*seg, segment_size*(seg+1))
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
        if form.do_stats.data:
            return stats(runner)
        listrunner_store[id_] = runner, time.time()
        return redirect(url_for('run'))
    return render_template('select.html', form=form)



class RunForm(Form):
    question = HiddenField()
    answer = StringField()

@app.route('/run/', methods=('GET', 'POST'))
def run():
    if 'id' not in session or session['id'] not in listrunner_store:
        flask.flash("Your stored ListRunner session has been lost (server restarted).")
        return redirect(url_for('select'))

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

        A = models.Answer(uid=current_user.get_id(),
                          sid=runner.session_id,
                          lid=runner.list_id,
                          q=results['q'],
                          a=results['a'],
                          c=results['c'],
                          correct=results['correct'])
        models.db.session.add(A)
        models.db.session.commit()
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

#@app.route('/stats/', methods=('GET', 'POST'))
def stats(runner):
    from sqlalchemy import func
    stats = [ ]
    header = ["Q", "A", "delay", "delay2"]
    uid = current_user.get_id()
    #raise ValueError
    #stats = models.db.session.query(models.Answer.q, models.Answer.c, func.count('*')).group_by(models.Answer.q)
    for q in runner.questions:
        q1 = models.Answer.query.filter_by(q=q,uid=uid).filter(models.Answer.correct==1).order_by('ts desc').limit(5).subquery()
        q2 = models.Answer.query.filter_by(q=q,uid=uid).filter(models.Answer.correct!=1).order_by('ts desc').limit(5).subquery()
        As = models.db.session.query(models.Answer).select_from(models.db.union_all(q1.select(), q2.select()))\
             .order_by('anon_1.ts desc').all()
        #print models.db.session.query(models.Answer).select_from(models.db.union_all(q1.select(), q2.select()))\
        #     .order_by('ts desc')
        #print
        #x = models.Answer.query.filter(models.Answer.correct!=1).limit(5).subquery().union(
        #    models.Answer.query.filter(models.Answer.correct!=1).limit(5).subquery()).order_by(models.Answer.ts).all()
        #print As

        # most recent correct answers
        x = models.db.session.execute("select max(a1.ts), max(a2.ts) from answer a1 join answer a2 using(q,uid) where a1.ts>a2.ts and q=:q and uid=:uid", dict(q=q, uid=uid))
        x = list(x)[0]
        import datetime
        #print x
        if x[0] is None or x[1] is None:
            delay = None
        else:
            x1 = datetime.datetime.strptime(x[0], '%Y-%m-%d %H:%M:%S.%f')
            x2 = datetime.datetime.strptime(x[1], '%Y-%m-%d %H:%M:%S.%f')
            delay = (x1-x2).total_seconds()

        # correct calculation of most recent correct answers
        delay2 = 0
        _t1 = None
        As.sort(key=lambda x: x.ts, reverse=True)
        #for A in As:
        #    print A.q, A.ts, A.correct
        for A in As:
            #print A.q, A.ts
            if A.correct != 1:
                break
            if _t1 is not None:
                delay2 = (_t1 - A.ts).total_seconds()
                break
            _t1 = A.ts

        x = models.db.session.execute("select max(ts), count(correct), sum(correct) FROM answer WHERE q=:q and uid=:uid GROUP BY sid ORDER BY max(ts) DESC", dict(q=q, uid=uid))
        goodness = [row[2]/float(row[1]) for row in x ]

        if len(As) > 0:
            stats.append((As[0].q, As[0].c, delay, delay2, goodness))
        else:
            stats.append((q, ))

    return render_template('stats.html', header=header, stats=stats)

@app.route("/login")
@login_required
def login():
    return "%s"%getattr(g, 'user', None)


if __name__ == '__main__':
    app.run(port=5001)

