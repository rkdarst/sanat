# Richard Darst, 2015

import itertools
import random
import re
import six
from six import iteritems

from django.contrib import messages

from . import config
from . import util
from . import models
from . import shingle


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
    def __init__(self, line, id=None, reverse=True, next_word_id=None):
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
        A = A.split(';')[0]
        A = re.sub('\([^)]*\)', '', A).strip()

        self.Q = Q
        self.A = A
        self.A_orig = A_orig
        self.word_id = next_word_id[0]  ; next_word_id[0] += 1

    def check(self, answer):
        def normalize(x):
            x = x.strip().lower()
            x.replace('.', '')
            x.replace('?', '')
            x.replace('!', '')
            x.replace('  ', ' ')
            return x
        if normalize(transform_unicode(answer)) == normalize(self.A):
            return True
        return False

class _ListRunner(object):
    def __str__(self):
        return 'ListRunner(%s)'%self.wordlist
    __repr__ = __str__
    def __init__(self, wordlist, **kwargs):
        self.shingler = None
        self.load_wordlist(wordlist, **kwargs)
        self.session_id = random.randint(0, 2**32-1)


    def load_wordlist(self, wordlist, from_english=False,
                      randomize=False, provide_choices=False, segment='all'):
        self.provide_choices = True
        #print "init ListRunner", wordlist
        self.wordlist = wordlist
        data = config.get_wordfile(wordlist)
        self.list_id = hash('file::'+wordlist)
        # Check if original file is reversed
        if '###reversed' in data[:512]:
            from_english = not from_english
        #
        data = data.split('\n')

        words = [ ]
        next_word_id = [ 0 ]  # this is a hack
        for line in data:
            try:
                words.append(Word(line, next_word_id=next_word_id, reverse=from_english))
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
        # Different levels of randomization
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
        self.shingler = shingle.Shingler(words=(x.A for x in all_words),
                                         n=(1,2,3))
        # Done with preprocessing.  Create standard data structures.
        self.words = words
        self.lookup = dict((word.serialize(), word) for word in words)
        self.lookup_a = dict((word.A, word) for word in words)

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
        if self.provide_choices:
            choices = self.shingler.find_count_similar(nextword.A, count=10)
            choices = list(choices)
            random.shuffle(choices)
        return nextword, dict(hint=choices)
    def answer(self, question, answer):
        word = self.lookup[question]
        was_correct = word.check(answer)
        #print self.wordstat
        self.wordstat[word.serialize()]['hist'].append(was_correct)

        # objects.get_or_create has problems with initial values, so
        # do the WordStatus creation or updating manually.
        try:
            word_status = models.WordStatus.objects.get(
                wlid=word.word_id,
                lid=self.list_id)
        except models.WordStatus.DoesNotExist:
            word_status = models.WordStatus(wlid=word.word_id,
                                            lid=self.list_id)
        word_status.answer(was_correct)
        word_status.save()

        # Generate the results data.
        if was_correct:
            self.wordstat[question]['r'] += 1
            return dict(was_correct=1,
                        word=word,
                        q=question, a=answer, c=word.A_orig.lower(),
                        )
        else:
            self.wordstat[question]['w'] += 1
            results = dict(was_correct=0,
                        word=word,
                        q=question, a=answer, c=word.A_orig.lower(),
                        diff=util.makediff(answer, word.A),
                        full_answer=word.A_orig)
            # find the closest answer.
            best_answer = self.shingler.find_count_similar(answer, count=1)
            if best_answer:
                best_answer = next(iter(best_answer))
                best_answer_word = self.lookup_a[best_answer]
                if best_answer_word.serialize() != question:
                    results['actual_answered_word'] = best_answer_word
            #
            return results


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


class V3(_ListRunner):
    def __init__(self, *args, **kwargs):
        # super-initialization
        super(V2, self).__init__(*args, **kwargs)

    def _next_question(self):
        asked_words = set()
        # anything old to check again?
        # FIXME: user
        max_seq = models.WordStatus.find_last_seq()
        words = models.WordStatus.objects.filter(lid=self.list_id).order_by('-last_ts')
        for asked in words:
            asked_words.add(words.wlid)
            if max_seq == words.wlid:
                continue
            if asked.c_short < .8:
                break
        else:
            # list exhausted
            pass



        return StopIteration
        #nextword = self.questions[self.i]
        #self.i += 1
        #global i
        #nextword = self.questions[i]
        #i += 1
        #print self.i
        return nextword

