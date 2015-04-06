# Richard Darst, 2015

import os

from flask import Markup # html escaping

import learn

def get_wordfiles():
    wordfiles = tuple((f, f) for f in sorted(
        x for x in os.listdir(learn.worddir)
        if not (x.endswith('~')
                or x.startswith('.')
                or x.startswith('#')
                or 'README' in x
                or x.startswith('_'))
        ))
    return wordfiles
def wordfile_filename(fname):
    return os.path.join(learn.worddir, fname)


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
                s1new.append(Markup(s1[i1:i2]))
                s2new.append(Markup(s2[j1:j2]))
        elif op == 'insert':
            s2new.extend(('<b>', Markup(s2[j1:j2]), '</b>'))
        elif op == "delete":
            s1new.extend(('<strike>', Markup(s1[i1:i2]), '</strike>'))
        elif op == 'replace':
            s1new.extend(('<strike>', Markup(s1[i1:i2]), '</strike>'))
            s2new.extend(('<b>', Markup(s2[j1:j2]), '</b>'))
        previousOp = op
        #if debug: print s1, s2
        #if debug: print "bottom"
    #if debug: print "done"
    return ''.join(s1new), ''.join(s2new)
