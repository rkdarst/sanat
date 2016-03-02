from django.shortcuts import render

# Create your views here.

# -*- coding: utf-8 -*-

# all the imports
import os
import random
import re
import sqlite3
import time

#import sys
#sys.path.append(os.path.dirname(__file__))
#sys.path.append('/srv/learn/pymod/')
#sys.path.append('/mnt/data1/srv/learn/venv/lib/python2.7/site-packages/')


#import flask
#from flask import Flask, request, session, g, redirect, url_for, \
#     abort, render_template, flash
#from flask import Markup # html escaping
#from flask_user import login_required, UserManager, UserMixin, SQLAlchemyAdapter
#from flask.ext.login import current_user #.get_id()

#from wtforms import Form, BooleanField, TextField, PasswordField, \
#     StringField, SelectField, SelectMultipleField, HiddenField, \
#     validators
#from flask_wtf import Form
#from django.forms import Form
from django.core.urlresolvers import reverse
import django.forms as forms
from django.forms import Form
from django.forms import BooleanField, \
     CharField, ChoiceField, MultipleChoiceField
from django.shortcuts import render, redirect

from . import ask_algs

from . import config
from . import models


randomize_options = [(0, 'Original word order'),
                     (2, 'Randomize locally'),
                     (1, 'Randomize fully'),
                      ]
class SelectorForm(Form):
    wordlist = ChoiceField(choices=config.list_wordfiles())
    #wordlist = forms.MultipleChoiceField(choices=wordfiles)
    from_english = BooleanField(initial=True, required=False)
    #randomize = BooleanField(label="Randomize fully", initial=False, required=False)
    #randomize_local = BooleanField(label="Randomize locally", initial=False, required=False)
    randomize = forms.ChoiceField(choices=randomize_options, widget=forms.RadioSelect(),
                                  initial=0)
    provide_choices = BooleanField(label='Provide hints?', initial=False, required=False)
    #segment = SelectField(default=False)
    segment = MultipleChoiceField(choices=[('all', 'All'), ], initial=['all'])
    alg = ChoiceField(label="Memorization algorithm")
    #do_list_words = BooleanField(initial=False, required=False, widget=forms.HiddenInput)
    #do_stats = BooleanField(initial=False, required=False, widget=forms.HiddenInput)

listrunner_store = { }

#@app.route('/', methods=('GET', 'POST'))
def select(request):
    Form = SelectorForm
    Form.base_fields['wordlist'].choices = config.list_wordfiles()
    # Set default wordlist to the last wordlist used
    Form.base_fields['alg'].choices = [(name, name) for name in ask_algs.list_algs()]

    # Compute options for segments (0-24, 25-30, etc)
    choices = [('all', 'All'), ]
    segment_size = 20
    for i in range(200//segment_size):
        choices.append((str(i), '% 3d-% 3d'%(segment_size*i, segment_size*(i+1)-1)))
    Form.base_fields['segment'].choices = choices

    if request.method == 'POST':
      form = SelectorForm(request.POST)
      if form.is_valid():
        wordlist = form.cleaned_data['wordlist']
        # store defaults so that we can pre-seed the form next time
        #request.session['wordlist'] = wordlist
        last_state = dict(form.cleaned_data) # copy
        last_state.pop('do_list_words', None)
        last_state.pop('do_stats', None)
        request.session['last_data'] = last_state
        #
        id_ = random.randint(0, 2**32-1)
        request.session['id'] = id_
        run_class = ask_algs.get_alg(form.cleaned_data['alg'])
        #randomize = 0
        #if form.cleaned_data['randomize_local']:
        #    randomize = 2
        #elif form.cleaned_data['randomize']:
        #    randomize = 1
        randomize = int(form.cleaned_data['randomize'])  # worst case: server error
        # segment
        segment = 'all'
        form_segment = form.cleaned_data['segment']
        if isinstance(form_segment, list) and form_segment[0] != 'all':
            # multi-select form
            segment = [ ]
            for seg in form.cleaned_data['segment']:
                seg = int(seg)
                segment.append((segment_size*seg, segment_size*(seg+1)))
        elif form_segment[0] != 'all':
            # single-select form
            seg = int(form_segment)
            segment = (segment_size*seg, segment_size*(seg+1))
        #request.session['ignored'] = [ ]
        runner = run_class(
            wordlist,
            from_english=form.cleaned_data['from_english'],
            randomize=randomize,
            segment=segment,
            provide_choices=form.cleaned_data['provide_choices'],
            )
        if 'do_list_words' in request.POST: #form.cleaned_data['do_list_words']:
            #import IPython ; IPython.embed()
            #form.data['do_list_words'] = False
            wordpairs = runner.words
            return render(request, 'select.html',
                          dict(form=form, wordpairs=wordpairs))
        if 'do_stats' in request.POST: #form.cleaned_data['do_stats']:
            return stats(runner)
        listrunner_store[id_] = runner, time.time()
        return redirect(reverse('run'), dict(form=form))
      else:
        # invalid form (should never happen, but if it does this ignores it.)
        pass
    form = SelectorForm(initial=request.session.get('last_data', {})   # defaults
                        )
    return render(request, 'select.html', dict(form=form))



class RunForm(Form):
    question = CharField(widget=forms.HiddenInput)
    answer = CharField(required=False)

#@app.route('/run/', methods=('GET', 'POST'))
def run(request):
    session = request.session
    if 'id' not in session or session['id'] not in listrunner_store:
        #flask.flash("Your stored ListRunner session has been lost (server restarted).")
        return redirect(reverse('select'))

    runner, creation_time = listrunner_store[session['id']]
    results = dict(was_correct=True)
    lastquestion = None
    newword_data = None
    context = c = { }
    c['was_correct'] = True

    if request.method == 'POST':
      form = RunForm(request.POST)
      if form.is_valid():
        last_question = c['last_question'] = form.cleaned_data['question']
        last_answer = form.cleaned_data['answer']
        if 'ignore' in request.POST:
            #request.session['ignored'].append(1)
            #runner.ignore(question)
            pass
        last_results = c['last_results'] = runner.answer(last_question, last_answer)

        A = models.Answer(user=request.user if not request.user.is_anonymous() else None,
                          sid=runner.session_id,
                          lid=runner.list_id,
                          q=last_results['q'],
                          a=last_results['a'],
                          c=last_results['c'],
                          correct=last_results['was_correct'])
        A.save()
    else:
        pass
    word, word_data = runner.question()
    c['word'] = word
    c['word_data'] = word_data
    if word == StopIteration:
        # Have some handling of the end of process...
        return redirect(reverse('select'))
    form = c['form'] = RunForm(initial=dict(question=word.serialize(), answer=None))
    #import IPython ; IPython.embed()

    return render(request, 'run.html', context)

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

    return render(request, 'stats.html', dict(header=header, stats=stats))

#@app.route("/login")
#@login_required
#def login():
#    return "%s"%getattr(g, 'user', None)




