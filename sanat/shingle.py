# Richard Darst, 2015.
from collections import defaultdict, Counter
import heapq
from six import iteritems

class Shingler(object):
    """Compute similarity between strings based on content.

    Shingles are substrings representing the content of a string.  For
    example, the string 'hello' is represented by the 2-shingles '',
    'el', 'll', 'lo'.  A hashtable based on shingles is made, and
    given an input word (e.g. 'help') similarity can be found by using
    lookup based on shingles ('he', 'el', 'lp', the first two shingles
    match).

    This is a quick and dirty shingler, that operates on an unchanging set
    of words.
    """

    def __init__(self, words, n=2, key=lambda x: x):
        """Initialize.

        n: shingle size, default 2
        words: iterable, shingle table initialized with this set.
        """
        if isinstance(n, int):
            n = (n, )
        self.n = n
        self.data = defaultdict(set)
        for word in words:
            self.add(word, key=key)
    def add(self, word, n=None, key=lambda x: x):
        for n in self.n:
            self._add(word, n, key=key)
    def _add(self, word, n=None, key=lambda x: x):
        """Add a word to the shingle table"""
        if n is None:
            n = self.n
        word_key = key(word)
        for i in range(len(word_key)-n+1):
            self.data[word_key[i:i+n]].add(word)

    def find_similar(self, word, n=None):
        """Find similar words, heaped by Jaccard score.

        Returns: heap of (-jacc, similar_word) pairs.
            To find most similar words, use
            neg_jacc, other_word = heapq.heappop(the_heap)
            repeatedly.
        """
        if n is None:
            n = max(self.n)
        similar = defaultdict(int)
        #for i in range(len(word)-self.n+1):
        #    shingle = word[i:i+self.n]
        for shingle in set(word[i:i+n] for i in range(len(word)-n+1)):
            for other_word in self.data.get(shingle, ()):
                similar[other_word] += 1
        # Be careful in normalization, since maximum number of
        # shingles in common is not `n`.
        jaccs = [(-overlap/float(len(word)+len(other_word)-overlap-2*(n-1)), other_word)
                 for other_word, overlap in iteritems(similar)]
        heapq.heapify(jaccs)
        return jaccs

    def find_count_similar(self, word, count=10):
        """Find a certain number of similar words, using an n."""
        choices = set()
        for n in self.n:
            jaccs = self.find_similar(word, n=n)
            #print n, jaccs
            while len(choices) < count and jaccs:
                jacc, hint = heapq.heappop(jaccs)
                if hint in choices: continue
                #if random.random() < .8: continue
                choices.add(hint)
                if len(choices) >= count:
                    break
            if len(choices) >= count:
                break
        return choices



