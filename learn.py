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
print sys.path

from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash

# configuration
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


worddir = '/srv/learn/data/'
def get_wordfiles():
    wordfiles = tuple((f, f) for f in sorted(
        x for x in os.listdir(worddir)
        if not (x.endswith('~')
                or x.startswith('.')
                or x.startswith('#'))
        ))
    return wordfiles

class ListRunner(object):
    shingle_data = { }
    def __str__(self):
        return 'ListRunner(%s)'%self.wordlist
    __repr__ = __str__
    def __init__(self, wordlist, from_english=False,
                 randomize=False, provide_choices=False, segment='all'):
        #print "init ListRunner", wordlist
        self.wordlist = wordlist
        data = open(worddir+wordlist).read().decode('utf-8').split('\n')
        # Check if original file is reversed
        if '###reversed' in open(worddir+wordlist).read(512):
            from_english = not from_english
        #
        data = [ l.strip() for l in data ]
        data = [ l for l in data if l and not l.startswith('#') ]
        # Split data into words, do basic pre-processing
        words = [ l.split('\\', 1) for l in data ]
        words = [ (x.strip(),y.strip()) for (x,y) in words
                  if x.strip() and y.strip()]  # ignore words missing a def.
        # Swap order if desired.  First word is question and second
        # word is answer.
        if from_english:
            words = [ (y,x) for (x,y) in words ]
        # Remove parenthesized groups from answers.
        words = [ (q, re.sub('\([^)]*\)', '', a).strip())
                  for q,a in words ]
        # Store all_data to use for shingling below
        all_words = words
        # if given data segment, only suggest the words from there.
        if segment is not None and segment != 'all':
            words = words[segment[0]: segment[1]]
        if randomize:
            # local randomization
            words2 = [ ]
            words.reverse()
            while words:
                i = random.randint(1, min(5, len(words)))
                words2.append(words.pop(-i))
            words = words2

        # If asked to provide choices, make shingles and store them
        if provide_choices:
            import shingle
            self.shingle_data[1] = shingle.Shingler(words=(x[1] for x in all_words),
                                                    n=1)
            self.shingle_data[2] = shingle.Shingler(words=(x[1] for x in all_words),
                                                    n=2)
            self.shingle_data[3] = shingle.Shingler(words=(x[1] for x in all_words),
                                                    n=3)
        # Done with preprocessing.  Create standard data structures.
        self.words = words
        self.questions = [ q for (q,v) in words ]
        self.answers = [ v for (q,v) in words ]
        #print self.answers
        #print self.answers
        self.lookup = dict(words)
        self.wordstat = dict([ (q, dict(r=0, w=0, hist=[], last=None))
                               for (q,v) in words ])
        self.count = 0
        self.countSecondRound = None
    def question(self):
        nextword = self._question_0()
        if nextword == StopIteration:
            return StopIteration, {}
        nextword_answer = self.lookup[nextword]
        choices = None
        if self.shingle_data:
            choices = set()
            n_choices = 10
            for n in (3, 2, 1):
                import heapq
                jaccs = self.shingle_data[n].find_similar(nextword_answer)
                #print n, jaccs
                while len(choices) < n_choices and jaccs:
                    jacc, hint = heapq.heappop(jaccs)
                    if hint in choices: continue
                    #if random.random() < .8: continue
                    choices.add(hint)
                    if len(choices) >= n_choices:
                        break
                if len(choices) >= n_choices:
                    break
            choices = list(choices)
            random.shuffle(choices)
        return nextword, dict(choices=choices)
    def _question_0(self):
        count = self.count
        self.count += 1
        for j in range(len(self.questions)):
            word = self.questions[j]
            stat = self.wordstat[word]
            if stat['last'] == count-1 and not j==len(self.questions)-1:
                # CONTINUE if presented last time, only if we aren't out.
                continue
            if len(stat['hist']) == 0:
                # if never been presented before
                stat['last'] = count
                return word
            if not stat['hist'][-1]:
                # if not correct on the last round
                stat['last'] = count
                return word
            if stat['last'] <= count-2 and not all(stat['hist'][-2:]):
                # get it right at least the last two times
                stat['last'] = count
                return word
        if self.countSecondRound is None:
            self.countSecondRound = count
        # Go through again and ensure:
        # - every word answered correct at least twice on the last round
        # - every word answered once in second round.
        for j in range(len(self.questions)):
            word = self.questions[j]
            stat = self.wordstat[word]
            if stat['last'] == count-1 and not j==len(self.questions)-1:
                # CONTINUE if presented last time, only if we aren't out.
                # Same condition on previous one.
                continue
            if not stat['hist'][-1]:
                # if not correct on the last round, do it again.
                stat['last'] = count
                return word
            if len(stat['hist']) < 2 or stat['last'] < self.countSecondRound:
                # Been seen at least once on second round, and correct
                # at least last two times.
                stat['last'] = count
                return word

        return StopIteration
        #nextword = self.questions[self.i]
        #self.i += 1
        #global i
        #nextword = self.questions[i]
        #i += 1
        #print self.i
        return nextword
    def answer(self, question, answer):
        correct = self.lookup[question].lower() == answer.lower()
        #print self.wordstat
        self.wordstat[question]['hist'].append(correct)
        if correct:
            self.wordstat[question]['r'] += 1
            return None
        else:
            self.wordstat[question]['w'] += 1
            return makediff(answer, self.lookup[question])


#class SelectorForm(forms.Form):
#    wordlist = forms.ChoiceField(choices=get_wordfiles())
#    #wordlist = forms.MultipleChoiceField(choices=wordfiles)
#    from_english = forms.BooleanField(initial=True)
#    randomize = forms.BooleanField(initial=False, required=False)

from wtforms import Form, BooleanField, TextField, PasswordField, \
     StringField, SelectField, HiddenField, validators
from flask_wtf import Form

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
    #print "select"
    #print session
    #from fitz import interactnow
    SelectorForm.wordlist.choices = get_wordfiles()
    #print get_wordfiles()
    #raise

    #form.field.

    form = SelectorForm(request.form)

    # Compute options for segments (0-24, 25-30, etc)
    choices = [('all', 'All'), ]
    segment_size = 25
    for i in range(500//segment_size):
        choices.append((str(i), '% 3d-% 3d'%(segment_size*i, segment_size*(i+1)-1)))
    form.segment.choices = choices

    if form.validate_on_submit():
        #print "valid"
        wordlist = form.wordlist.data
        #wordlist = wordlistwordfiles[int(wordlist)][1]
        #wordlist = wordlist[0]
        #print repr(wordlist)
        session['wordlist'] = wordlist
        id_ = random.randint(0, 2**32-1)
        session['id'] = id_
        runner = ListRunner(
            wordlist,
            from_english=form.from_english.data,
            randomize=form.randomize.data,
            segment=(segment_size*int(form.segment.data), segment_size*(int(form.segment.data)+1)-1) if form.segment.data!='all' else 'all',
            provide_choices=form.provide_choices.data,
            )
        listrunner_store[id_] = runner, time.time()
        #print session
        #session.modified = True

        #print form._fields
        #raise
        #from fitz import interact ; interact.interact()
        if form.list_words.data:
        #    print "listing all words"
            wordpairs = runner.words
        #    #HttpResponseRedirect('')
            return render_template('select.html', form=form, wordpairs=wordpairs)
        #    print "x"*100
        return redirect(url_for('run'))
    #else:
    #    form = SelectorForm()
        #form.fields['wordlist']._set_choices(get_wordfiles())

    #return HttpResponse('test')
    return render_template('select.html', form=form)

#class RunForm(forms.Form):
#    question= forms.CharField(
#        widget=forms.HiddenInput
#        )
#    answer = forms.CharField(required=False)

class RunForm(Form):
    question = HiddenField()
    answer = StringField()


@app.route('/run/', methods=('GET', 'POST'))
def run():
    #print 'run'
    #print session
    #print repr(session['id'])
    #print listrunner_store
    runner, creation_time = listrunner_store[session['id']]
    diff = None
    lastquestion = None
    newword_data = None
    #raise

    form = RunForm()
    if form.validate_on_submit():
        question = form.question.data
        lastquestion = question
        answer = form.answer.data
        if u'ignore' in form.data:
            #print "ignoring word"
            runner.ignore(question)
        diff = runner.answer(question, answer)

        # re-create the form
        #newword, newword_data = runner.question()
        #form = RunForm(formdata=None,
        #               data=dict(question=newword, answer=None))
    else:
        pass
    newword, newword_data = runner.question()
    if newword == StopIteration:
        # Have some handling of the end of process...
        return redirect(url_for('select'))
    form = RunForm(formdata=None,
                   data=dict(question=newword, answer=None))

    #session['obj'] = runner
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
                s1new.append(s1[i1:i2])
                s2new.append(s2[j1:j2])
        elif op == 'insert':
            s2new.extend(('<b>', s2[j1:j2], '</b>'))
        elif op == "delete":
            s1new.extend(('<strike>', s1[i1:i2], '</strike>'))
        elif op == 'replace':
            s1new.extend(('<strike>', s1[i1:i2], '</strike>'))
            s2new.extend(('<b>', s2[j1:j2], '</b>'))
        previousOp = op
        #if debug: print s1, s2
        #if debug: print "bottom"
    #if debug: print "done"
    return ''.join(s1new), ''.join(s2new)






if __name__ == '__main__':
    app.run()

