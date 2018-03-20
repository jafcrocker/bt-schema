import unittest
from message import onMessage, onMessageConcurrent, Context
from table import Table, RTSKey, TransitionsKey

rts_exp = lambda x,y: [((x,-i),[]) for i in y]
tr_exp = lambda x,y: [((x,-i,-j),None) for i,j in y]


class TestMessage(unittest.TestCase):
    def setUp(self):
        RTS=Table(RTSKey)
        Transitions=Table(TransitionsKey)
        self.ctx = Context(RTS, Transitions)

    def test_initial(self):
        onMessage('n', 1, [], self.ctx)
        rts = self.ctx.RTS.prefix('n')
        tr = self.ctx.Transitions.prefix('n')
        self.assertEqual(rts, [(('n',-1),[])])
        self.assertEqual(tr, [(('n',0,-1),None)])

    def test_sequential(self):
        onMessage('n', 1, [], self.ctx)
        onMessage('n', 2, [], self.ctx)
        onMessage('n', 3, [], self.ctx)
        rts = self.ctx.RTS.prefix('n')
        tr = self.ctx.Transitions.prefix('n')
        expected = [(('n', i),[]) for i in range (-3,0)]
        self.assertEqual(rts, expected)
        expected = [(('n',i,i-1),None) for i in (-2,-1,0)]
        self.assertEqual(tr, expected)

    def test_outOfOrder(self):
        onMessage('n', 1, [], self.ctx)
        onMessage('n', 3, [], self.ctx)
        onMessage('n', 2, [], self.ctx)
        rts = self.ctx.RTS.prefix('n')
        tr = self.ctx.Transitions.prefix('n')
        expected = [(('n', i),[]) for i in range (-3,0)]
        self.assertEqual(rts, expected)
        expected = [(('n',i,i-1),None) for i in (-2,-1,0)]
        self.assertEqual(tr, expected)

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
        with self.assertRaises(StopIteration): t2.next()
        with self.assertRaises(StopIteration): t3.next()
        self.assertEqual(rts(), rts_exp('n', (4,3,2,1)))
        self.assertEqual(trs(), tr_exp('n', ((3,4),(2,3),(1,2),(0,1))))
