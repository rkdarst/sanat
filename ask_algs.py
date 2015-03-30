# Richard Darst, 2015

import random
import re

import learn
import util

class _ListRunner(object):
    def __str__(self):
        return 'ListRunner(%s)'%self.wordlist
    __repr__ = __str__
    def __init__(self, wordlist, **kwargs):

        self.shingle_data = { }
        self.load_wordlist(wordlist, **kwargs)


    def load_wordlist(self, wordlist, from_english=False,
                      randomize=False, provide_choices=False, segment='all'):
        #print "init ListRunner", wordlist
        self.wordlist = wordlist
        data = open(util.wordfile_filename(wordlist)).read().decode('utf-8').split('\n')
        # Check if original file is reversed
        if '###reversed' in open(util.wordfile_filename(wordlist)).read(512):
            from_english = not from_english
        #
        data = [ l.strip() for l in data ]
        data = [ l for l in data if l and not l.startswith('#') ]
        # Split data into words, do basic pre-processing
        words = [ l.split('\\', 1) for l in data ]
        words = [ x for x in words if len(x) == 2 ]
        words = [ (x.strip(),y.strip()) for (x,y) in words
                  if x.strip() and y.strip()]  # ignore words missing a def.
        # Swap order if desired.  First word is question and second
        # word is answer.
        if from_english:
            words = [ (y,x) for (x,y) in words ]
        # Remove parenthesized groups from answers.  Leave original
        # answer on the end.
        words = [ (q, re.sub('\([^)]*\)', '', a).strip(), a)
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
        self.questions, self.answers, self.answers_full = zip(*words)

        self.lookup = dict((q, (a, fa)) for (q,a,fa) in words)
    def question(self):
        nextword = self._next_question()
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
    def answer(self, question, answer):
        correct = self.lookup[question][0].lower() == answer.lower()
        #print self.wordstat
        self.wordstat[question]['hist'].append(correct)
        if correct:
            self.wordstat[question]['r'] += 1
            return dict(correct=True)
        else:
            self.wordstat[question]['w'] += 1
            return dict(correct=False,
                        diff=util.makediff(answer, self.lookup[question][0]),
                        full_answer=self.lookup[question][1])


class ListRunner(_ListRunner):
    def __init__(self, *args, **kwargs):
        # super-initialization
        super(ListRunner, self).__init__(*args, **kwargs)

        self.wordstat = dict([ (q, dict(r=0, w=0, hist=[], last=None))
                               for q in self.questions ])
        self.count = 0
        self.countSecondRound = None


    def _next_question(self):
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

