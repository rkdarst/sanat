# Richard Darst, 2015.
from collections import defaultdict, Counter
import heapq

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

    def __init__(self, words, n=2):
        """Initialize.

        n: shingle size, default 2
        words: iterable, shingle table initialized with this set.
        """
        self.n = n
        self.data = defaultdict(set)
        for word in words:
            self.add(word)
    def add(self, word):
        """Add a word to the shingle table"""
        for i in range(len(word)-self.n+1):
            self.data[word[i:i+self.n]].add(word)

    def find_similar(self, word):
        """Find similar words, heaped by Jaccard score.

        Returns: heap of (-jacc, similar_word) pairs.
            To find most similar words, use
            neg_jacc, other_word = heapq.heappop(the_heap)
            repeatedly.
        """
        similar = defaultdict(int)
        #for i in range(len(word)-self.n+1):
        #    shingle = word[i:i+self.n]
        for shingle in set(word[i:i+self.n] for i in range(len(word)-self.n+1)):
            for other_word in self.data.get(shingle, ()):
                similar[other_word] += 1
        # Be careful in normalization, since maximum number of
        # shingles in common is not `n`.
        jaccs = [(-overlap/float(len(word)+len(other_word)-overlap-2*(self.n-1)), other_word)
                 for other_word, overlap in similar.iteritems()]
        heapq.heapify(jaccs)
        return jaccs





