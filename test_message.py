import unittest
from message import onMessage, onMessageConcurrent, Context, MAXINT
from table import Table, RTSKey, TransitionsKey, RRTSKey

rts_exp = lambda x,y: [(RTSKey(x,-i),[]) for i in y]
tr_exp = lambda x,y: [(TransitionsKey(x,-i,-j),None) for i,j in y]


class TestMessage(unittest.TestCase):
    def setUp(self):
        RTS=Table(RTSKey)
        RRTS=Table(RRTSKey)
        Transitions=Table(TransitionsKey)
        self.ctx = Context(RTS, RRTS, Transitions)

    def test_initial(self):
        onMessage('n', 1, [], self.ctx)
        rts = self.ctx.RTS.prefix('n')
        tr = self.ctx.Transitions.prefix('n')
        self.assertEqual(rts, rts_exp('n', (MAXINT,1,0)))
        self.assertEqual(tr, tr_exp('n',((1,9),(0,1))))

    def test_sequential(self):
        onMessage('n', 1, [], self.ctx)
        onMessage('n', 2, [], self.ctx)
        onMessage('n', 3, [], self.ctx)
        rts = self.ctx.RTS.prefix('n')
        tr = self.ctx.Transitions.prefix('n')
        self.assertEqual(rts, rts_exp('n',(MAXINT,3,2,1,0)))
        self.assertEqual(tr, tr_exp('n', ((3,9),(2,3),(1,2),(0,1))))

    def test_outOfOrder(self):
        onMessage('n', 1, [], self.ctx)
        onMessage('n', 3, [], self.ctx)
        onMessage('n', 2, [], self.ctx)
        rts = self.ctx.RTS.prefix('n')
        tr = self.ctx.Transitions.prefix('n')
        self.assertEqual(rts, rts_exp('n',(MAXINT,3,2,1,0)))
        self.assertEqual(tr, tr_exp('n', ((3,9),(2,3),(1,2),(0,1))))

"""
    def test_concurrent(self):
        rts = lambda: self.ctx.RTS.prefix('n')
        trs = lambda: self.ctx.Transitions.prefix('n')
        onMessage('n', 1, [], self.ctx)
        onMessage('n', 4, [], self.ctx)
        t2 = onMessageConcurrent('n', 2, [], self.ctx)
        t3 = onMessageConcurrent('n', 3, [], self.ctx)
        self.assertEqual(rts(), rts_exp('n',(4,1)))
        self.assertEqual(trs(), tr_exp('n', ((1,4),(0,1))))
        # 1 (Write to RTS)
        t2.next()
        t3.next()
        self.assertEqual(rts(), rts_exp('n', (4,3,2,1)))
        self.assertEqual(trs(), tr_exp('n', ((1,4),(0,1))))
        # 2 (Read previous state from RTS)
        t2.next()
        t3.next()
        # 3 (Write to Transitions)
        t2.next()
        t3.next()
        self.assertEqual(rts(), rts_exp('n', (4,3,2,1)))
        self.assertEqual(trs(), tr_exp('n', ((2,3),(1,4),(1,2),(0,1))))
        # 4 (Read transitions)
        t2.next()
        t3.next()
        # 5 (Read messages)
        t2.next()
        t3.next()
        # 6 (Fix up)
        self.assertEqual(rts(), rts_exp('n', (4,3,2,1)))
        self.assertEqual(trs(), tr_exp('n', ((2,3),(1,4),(1,2), (0,1))))
        t2.next()
        t3.next()
        self.assertEqual(rts(), rts_exp('n', (4,3,2,1)))
        self.assertEqual(trs(), tr_exp('n', ((3,4),(2,3),(1,2),(0,1))))
        with self.assertRaises(StopIteration): t2.next()
        with self.assertRaises(StopIteration): t3.next()
"""
"""
class MyTestsMeta(type):
    def __new__(cls, name, bases, attrs):
        for a in range(0,7):
            for b in range(a,7):
                for c in range(b,7):
                    for d in range(c,7):
                        for e in range(d,7):
                            for f in range(e,7):
                                name,fn = cls.gen(a,b,c,d,e,f)
                                attrs[name] = fn

        return super(MyTestsMeta, cls).__new__(cls, name, bases, attrs)

    @classmethod
    def gen(cls, *args):
        # Return a testcase that tests (a,b,c,d,e,f).
        assert len(args) == 6 and min(args) >= 0 and max(args) <= 6
        name = ''.join(str(i) for i in args)
        def fn(self):
            self.assertEqual(self.doit(args), None)
        return 'test_'+name, fn

class MyTests(unittest.TestCase):
    __metaclass__ = MyTestsMeta
    def setUp(self):
        RTS=Table(RTSKey)
        Transitions=Table(TransitionsKey)
        self.ctx = Context(RTS, Transitions)

    def doit(self, order):
        onMessage('n', 1, [], self.ctx)
        onMessage('n', 4, [], self.ctx)
        t2 = onMessageConcurrent('n', 2, [], self.ctx)
        t3 = onMessageConcurrent('n', 3, [], self.ctx)

        for i in range(7):
            for j in range(6):
                if order[j]==i:
                    t3.next()
            if i != 6:
                t2.next()

        with self.assertRaises(StopIteration): t2.next()
        with self.assertRaises(StopIteration): t3.next()
        self.assertEqual(self.ctx.RTS.prefix('n'), 
                rts_exp('n', (4,3,2,1)))
        self.assertEqual(self.ctx.Transitions.prefix('n'), 
                tr_exp('n', ((3,4),(2,3),(1,2),(0,1))))
"""
