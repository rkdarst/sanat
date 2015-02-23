# all the imports
import os
import random
import sqlite3
import time

from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash

# configuration
#DATABASE = '/tmp/flaskr.db'
DEBUG = True
SECRET_KEY = 'tnaou64oatn!#%>ntao64\ue7!$%$%@!ouiuueau'
#USERNAME = 'admin'
#PASSWORD = 'default'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)


worddir = '/home/richard/learn/data/'
def get_wordfiles():
    wordfiles = tuple((f, f) for f in sorted(
        x for x in os.listdir(worddir)
        if not (x.endswith('~')
                or x.startswith('.')
                or x.startswith('#'))
        ))
    return wordfiles

class ListRunner(object):
    def __str__(self):
        return 'ListRunner(%s)'%self.wordlist
    __repr__ = __str__
    def __init__(self, wordlist, from_english=False,
                 randomize=False):
        print "init ListRunner", wordlist
        self.wordlist = wordlist
        data = open(worddir+wordlist).read().decode('utf-8').split('\n')
        data = [ l.strip() for l in data ]
        data = [ l for l in data if l and not l.startswith('#') ]
        words = [ l.split('\\', 1) for l in data ]
        words = [ (x.strip(),y.strip()) for (x,y) in words ]
        print words
        if from_english:
            words = [ (y,x) for (x,y) in words ]
        self.words = words
        self.questions = [ q for (q,v) in words ]
        self.answers = [ v for (q,v) in words ]
        self.lookup = dict(words)
        self.wordstat = dict([ (q, dict(r=0, w=0, hist=[], last=None))
                               for (q,v) in words ])
        self.count = 0
        self.countSecondRound = None
    def question(self):
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
        print self.i
        return nextword
    def answer(self, question, answer):
        correct = self.lookup[question].lower() == answer.lower()
        print self.wordstat
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
    list = BooleanField(default=False)

listrunner_store = { }

@app.route('/', methods=('GET', 'POST'))
def select():
    print "select"
    print session
    #from fitz import interactnow
    SelectorForm.wordlist.choices = get_wordfiles()
    #print get_wordfiles()
    #raise

    #form.field.

    form = SelectorForm(request.form)
    if form.validate_on_submit():
        print "valid"
        wordlist = form.wordlist.data
        #wordlist = wordlistwordfiles[int(wordlist)][1]
        #wordlist = wordlist[0]
        print repr(wordlist)
        session['wordlist'] = wordlist
        id_ = random.randint(0, 2**32-1)
        session['id'] = id_
        runner = ListRunner(
            wordlist,
            from_english=form.from_english.data,
            randomize=form.randomize.data,
            )
        listrunner_store[id_] = runner, time.time()
        print session
        #session.modified = True

        #print form._fields
        #raise
        #from fitz import interact ; interact.interact()
        if form.list.data:
        #    print "listing all words"
            wordpairs = runner.words
        #    #HttpResponseRedirect('')
            return render_template('select.html', form=form, wordpairs=wordpairs)
        #    print "x"*100
        return redirect('/run/')
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
    print 'run'
    print session
    print repr(session['id'])
    print listrunner_store
    runner, creation_time = listrunner_store[session['id']]
    diff = None
    lastquestion = None
    #raise

    form = RunForm()
    if form.validate_on_submit():
        question = form.question.data
        lastquestion = question
        answer = form.answer.data
        if u'ignore' in form.data:
            print "ignoring word"
            runner.ignore(question)
        diff = runner.answer(question, answer)

        # re-create the form
        newword = runner.question()
        form = RunForm(formdata=None,
                       data=dict(question=newword, answer=None))
    else:
        newword = runner.question()
        form = RunForm(formdata=None,
                       data=dict(question=newword, answer=None))

    #session['obj'] = runner
    session.modified = True
    return render_template('run.html',
                           form=form, diff=diff, newword=newword,
                           lastquestion=lastquestion)


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

