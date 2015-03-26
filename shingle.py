# Richard Darst, 2015.
from collections import defaultdict, Counter
import heapq

class Shingler(object):
    def __init__(self, words, n=2):
        self.n = n
        self.data = defaultdict(list)
        for word in words:
            self.add(word)
    def add(self, word):
        for i in range(len(word)-self.n+1):
            self.data[word[i:i+self.n]].append(word)

    def find_similar(self, word):
        similar = defaultdict(int)
        #for i in range(len(word)-self.n+1):
        #    shingle = word[i:i+self.n]
        for shingle in set(word[i:i+self.n] for i in range(len(word)-self.n+1)):
            for other_word in self.data.get(shingle, ()):
                similar[other_word] += 1
        jaccs = [(-overlap/float(len(word)+len(other_word)-overlap-2*(self.n-1)), other_word)
                 for other_word, overlap in similar.iteritems()]
        heapq.heapify(jaccs)
        return jaccs





