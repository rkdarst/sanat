# Richard Darst, 2015

import itertools
import random
import re
import six
from six import iteritems

#import learn
from . import config
from . import util

from django.contrib import messages

def list_algs():
    """List all memorization argorithms available"""
    return sorted(name for name, obj in iteritems(globals())
                  if isinstance(obj, type)
                     if issubclass(obj, _ListRunner)
                     and not obj==_ListRunner )
def get_alg(name):
    """Get a memorization algorithm by name"""
    return globals()[name]

def transform_unicode(ans):
    ans.replace('"a"', u'ä')
    ans.replace('"A"', u'Ä')
    ans.replace('"o"', u'ö')
    ans.replace('"O"', u'Ö')
    return ans
class DoNotUseWord(Exception):
    pass
class Word(object):
    def __hash__(self):
        return hash(self._line)
    def serialize(self):
        """Used in wordlist.lookup[]"""
        return self.Q
    def __init__(self, line, id=None, reverse=True):
        self._line = line
        line = line.strip()
        if line.startswith('#'):
            raise DoNotUseWord()
        # Split data into words, do basic pre-processing
        words = line.split('\\', 1)
        if len(words) < 2:
            raise DoNotUseWord()
        Q, A = words
        Q = Q.strip()
        A = A.strip()
        if not Q or not A:
            raise DoNotUseWord()
        # Swap order if desired.  First word is question and second
        # word is answer.
        if reverse:
            Q, A = A, Q
        # Remove parenthesized groups from answers.  Leave original
        # answer on the end.
        A_orig = A
        A = re.sub('\([^)]*\)', '', A_orig).strip()

        self.Q = Q
        self.A = A
        self.A_orig = A_orig

    def check(self, answer):
        if transform_unicode(answer.lower()) == self.A.lower():
            return True
        return False

class _ListRunner(object):
    def __str__(self):
        return 'ListRunner(%s)'%self.wordlist
    __repr__ = __str__
    def __init__(self, wordlist, **kwargs):

        self.shingle_data = { }
        self.load_wordlist(wordlist, **kwargs)
        self.session_id = random.randint(0, 2**32-1)


    def load_wordlist(self, wordlist, from_english=False,
                      randomize=False, provide_choices=False, segment='all'):
        #print "init ListRunner", wordlist
        self.wordlist = wordlist
        data = config.get_wordfile(wordlist)
        self.list_id = hash(wordlist)
        # Check if original file is reversed
        if '###reversed' in data[:512]:
            from_english = not from_english
        #
        data = data.split('\n')

        words = [ ]
        for line in data:
            try:
                words.append(Word(line))
            except DoNotUseWord:
                pass

        # Store all_data to use for shingling below
        all_words = words
        # if given data segment, only suggest the words from there.
        if segment is not None and segment != 'all':
            if isinstance(segment[0], tuple):
                # multi-select form
                words2 = [ ]
                for seg in segment:
                    words2.extend(words[seg[0]: seg[1]])
                words = words2
            else:
                # single-select form
                words = words[segment[0]: segment[1]]
        if randomize == 2:
            # local randomization
            words2 = [ ]
            words.reverse()
            while words:
                i = random.randint(1, min(5, len(words)))
                words2.append(words.pop(-i))
            words = words2
        elif randomize:
            # full randomization
            random.shuffle(words)

        # If asked to provide choices, make shingles and store them
        if provide_choices:
            import shingle
            self.shingle_data[1] = shingle.Shingler(words=(x.A for x in all_words),
                                                    n=1)
            self.shingle_data[2] = shingle.Shingler(words=(x.A for x in all_words),
                                                    n=2)
            self.shingle_data[3] = shingle.Shingler(words=(x.A for x in all_words),
                                                    n=3)
        # Done with preprocessing.  Create standard data structures.
        self.words = words
        #if len(words) != 0:
        #    self.questions, self.answers, self.answers_full = zip(*words)
        #else:
        #    self.questions = self.answers = self.answers_full = [ ]

        self.lookup = dict((word.serialize(), word) for word in words)
    def question(self):
        """Get the next question.

        - Call self._nextword(), which is overridden in subclasses.
        - Compute shingle data, for hints.
        - Return (Word, data).  Data should be passed to the form, has hints and so on."""
        if len(self.words) == 0:
            #messages.add_message(request, messages.INFO, "There are no words in this list.")
            print("There are no words in this list.")
            return StopIteration, {}
        nextword = self._next_question()
        if nextword == StopIteration:
            return StopIteration, {}
        #nextword_answer = self.lookup[hash(nextword)]
        choices = None
        if self.shingle_data:
            choices = set()
            n_choices = 10
            for n in (3, 2, 1):
                import heapq
                jaccs = self.shingle_data[n].find_similar(nextword.A)
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
    def answer(self, question, answer):
        asked_word = self.lookup[question]
        correct = asked_word.check(answer)
        #print self.wordstat
        self.wordstat[asked_word.serialize()]['hist'].append(correct)
        if correct:
            self.wordstat[question]['r'] += 1
            return dict(correct=1,
                        q=question, a=answer, c=self.lookup[question].A_orig.lower())
        else:
            self.wordstat[question]['w'] += 1
            return dict(correct=0,
                        q=question, a=answer, c=self.lookup[question].A_orig.lower(),
                        diff=util.makediff(answer, self.lookup[question].A),
                        full_answer=self.lookup[question].A_orig)


class Original(_ListRunner):
    def __init__(self, *args, **kwargs):
        # super-initialization
        super(Original, self).__init__(*args, **kwargs)

        self.wordstat = dict((word.serialize(), dict(r=0, w=0, hist=[], last=None))
                              for word in self.words )
        self.count = 0
        self.countSecondRound = None


    def _next_question(self):
        count = self.count
        self.count += 1
        for j in range(len(self.words)):
            word = self.words[j]
            stat = self.wordstat[word.serialize()]
            if stat['last'] == count-1 and not j==len(self.words)-1:
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
        for j in range(len(self.words)):
            word = self.words[j]
            stat = self.wordstat[word.serialize()]
            if stat['last'] == count-1 and not j==len(self.words)-1:
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


class V2(_ListRunner):
    def __init__(self, *args, **kwargs):
        # super-initialization
        super(V2, self).__init__(*args, **kwargs)

        self.wordstat = dict([ (q, dict(r=0, w=0, hist=[], last=0))
                               for q in self.questions ])
        self.nwords = len(self.questions)
        self.i = 0
        self.next = 0
        self.countSecondRound = None


    def _next_question(self):
        i = count = self.i
        self.i += 1
        for j in range(self.next, -1, -1):
        #for j in range(len(self.questions)):
            word = self.questions[j]
            stat = self.wordstat[word]

            # What is the current status of this word?
            n_times_right = sum(1 for _ in
                 itertools.takewhile(lambda x: x, reversed(stat['hist'])))
            if n_times_right > 4:
                continue
            # delay size
            delay_size = n_times_right
            print(i, n_times_right, delay_size, stat['last'], stat)
            if i >= stat['last'] + delay_size:
                stat['last'] = i
                return word

        #word = 

            #if stat['last'] == count-1 and not j==len(self.questions)-1:
            #    # CONTINUE if presented last time, only if we aren't out.
            #    continue
            #if len(stat['hist']) == 0:
            #    # if never been presented before
            #    stat['last'] = count
            #    return word
            #if not stat['hist'][-1]:
            #    # if not correct on the last round
            #    stat['last'] = count
            #    return word
            #if stat['last'] <= count-2 and not all(stat['hist'][-2:]):
            #    # get it right at least the last two times
            #    stat['last'] = count
            #    return word
        if self.countSecondRound is None:
            self.countSecondRound = count
        # Go through again and ensure:
        # - every word answered correct at least twice on the last round
        # - every word answered once in second round.
        #for j in range(len(self.questions)):
        #    word = self.questions[j]
        #    stat = self.wordstat[word]
        #    if stat['last'] == count-1 and not j==len(self.questions)-1:
        #        # CONTINUE if presented last time, only if we aren't out.
        #        # Same condition on previous one.
        #        continue
        #    if not stat['hist'][-1]:
        #        # if not correct on the last round, do it again.
        #        stat['last'] = count
        #        return word
        #    if len(stat['hist']) < 2 or stat['last'] < self.countSecondRound:
        #        # Been seen at least once on second round, and correct
        #        # at least last two times.
        #        stat['last'] = count
        #        return word

        return StopIteration
        #nextword = self.questions[self.i]
        #self.i += 1
        #global i
        #nextword = self.questions[i]
        #i += 1
        #print self.i
        return nextword

