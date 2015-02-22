# all the imports
import sqlite3
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
    def __init__(self, wordlist, from_english=False,
                 randomize=False):
        print "init ListRunner"
        self.wordlist = wordlist
        data = open(worddir+wordlist).read().decode('utf-8').split('\n')
        data = [ l.strip() for l in data ]
        data = [ l for l in data if l and not l.startswith('#') ]
        words = [ l.split('\\', 1) for l in data ]
        words = [ (x.strip(),y.strip()) for (x,y) in words ]
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


class SelectorForm(forms.Form):
    wordlist = forms.ChoiceField(choices=get_wordfiles())
    #wordlist = forms.MultipleChoiceField(choices=wordfiles)
    from_english = forms.BooleanField(initial=True)
    randomize = forms.BooleanField(initial=False, required=False)

@app.route('/')
def select(request):
    print "select"
    #from fitz import interactnow
    SelectorForm.base_fields['wordlist']._set_choices(get_wordfiles())
    #form.field.

    if request.method == 'POST':
        form = SelectorForm(request.POST)
        #form.fields['wordlist']._set_choices(get_wordfiles())
        if form.is_valid():
            wordlist = form.cleaned_data['wordlist']
            #wordlist = wordlistwordfiles[int(wordlist)][1]
            #wordlist = wordlist[0]
            request.session['wordlist'] = wordlist
            request.session['obj'] = ListRunner(
                wordlist,
                from_english=form.cleaned_data['from_english'],
                randomize=form.cleaned_data['randomize'],
                )
            #from fitz import interact ; interact.interact()
            if u'list' in form.data:
                print "listing all words"
                wordpairs = request.session['obj'].words
                #HttpResponseRedirect('')
                return render_to_response('select.html', locals(),
                                   context_instance=RequestContext(request))
                print "x"*100
            return HttpResponseRedirect('/run/')
    else:
        form = SelectorForm()
        #form.fields['wordlist']._set_choices(get_wordfiles())

    #return HttpResponse('test')
    return render_to_response('select.html', locals(),
                              context_instance=RequestContext(request))

class RunForm(forms.Form):
    question= forms.CharField(
        widget=forms.HiddenInput
        )
    answer = forms.CharField(required=False)

@app.route('/run')
def run(request):
    session = request.session
    runner = request.session['obj']

    if request.method == 'POST':
        print "post"
        form = RunForm(request.POST)
        if form.is_valid():
            print "valid"
            question = form.cleaned_data['question']
            lastquestion = question
            answer = form.cleaned_data['answer']
            if u'ignore' in form.data:
                print "ignoring word"
                runner.ignore(question)
            diff = runner.answer(question, answer)
            #print answer, diff
        # re-create the form
        newword = runner.question()
        form = RunForm(initial=dict(question=newword))
        form.fields['question'].initial = newword
        print newword
#            return HttpResponseRedirect('/run/')
    else:
        #correct = True
        #print "get"
        #diff = '<null>', '<null>'
        newword = runner.question()
        form = RunForm(initial=dict(question=newword))

    session['obj'] = runner
    return render_to_response('run.html', locals(),
                              context_instance=RequestContext(request))

    pass


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

