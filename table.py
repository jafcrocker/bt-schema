from collections import namedtuple

class RTSKey (namedtuple('RTSKey', ('node', 'time'))):
    def __repr__(self):
        return '#'.join((self[0], str(-self[1])))

class TransitionsKey(namedtuple('TransitionsKey', ('node', 'precedent', 'subsequent'))):
    def __repr__(self):
        return "{}#{}#{}".format(self[0], -self[1], -self[2])


class Table(object):
    def __init__(self, keyClass):
        self.keyClass = keyClass
        self._table={}
    def insert(self, key, val):
        key = self.keyClass(*key)
        self._table[key] = val
    def delete(self, key):
        key = self.keyClass(*key)
        self._table.pop(key, None)
    def scan(self, begin, end, inclusive=False):
        begin,end = self.keyClass(*begin), self.keyClass(*end)
        in_range = (lambda x: x >= begin and x < end ) if not inclusive else \
                   (lambda x: x >= begin and x <= end)
        return [(k,v) for k,v in sorted(self._table.items()) if in_range(k)]
    def prefix(self, key):
        matches = lambda x: all(i==j for i,j in zip(key,x))
        return [(k,v) for k,v in sorted(self._table.items()) if matches(k)]
    def __str__(self):
        return '{' + ','.join(repr(i) for i in sorted(self._table.keys())) + '}'
