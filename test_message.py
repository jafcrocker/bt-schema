import unittest
from message import onMessage, onMessageConcurrent, Context, MAXINT as MAX
from table import Table, RTSKey, TransitionsKey, RRTSKey

rts_exp = lambda x,y: [(RTSKey(x,-i),[]) for i in y]
rrts_exp = lambda x,y: [(RRTSKey(x,i),0) for i in y]
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
        self.assertEqual(rts, rts_exp('n', (MAX,1,0)))
        self.assertEqual(tr, tr_exp('n',((1,MAX),(0,1))))

    def test_sequential(self):
        onMessage('n', 1, [], self.ctx)
        onMessage('n', 2, [], self.ctx)
        onMessage('n', 3, [], self.ctx)
        rts = self.ctx.RTS.prefix('n')
        tr = self.ctx.Transitions.prefix('n')
        self.assertEqual(rts, rts_exp('n',(MAX,3,2,1,0)))
        self.assertEqual(tr, tr_exp('n', ((3,MAX),(2,3),(1,2),(0,1))))

    def test_outOfOrder(self):
        onMessage('n', 1, [], self.ctx)
        onMessage('n', 3, [], self.ctx)
        onMessage('n', 2, [], self.ctx)
        rts = self.ctx.RTS.prefix('n')
        tr = self.ctx.Transitions.prefix('n')
        self.assertEqual(rts, rts_exp('n',(MAX,3,2,1,0)))
        self.assertEqual(tr, tr_exp('n', ((3,MAX),(2,3),(1,2),(0,1))))

    def test_concurrent(self):
        rts = lambda: self.ctx.RTS.prefix('n')
        rrts = lambda: self.ctx.RRTS.prefix('n')
        trs = lambda: self.ctx.Transitions.prefix('n')
        onMessage('n', 1, [], self.ctx)
        onMessage('n', 4, [], self.ctx)
        t2 = onMessageConcurrent('n', 2, [], self.ctx)
        t3 = onMessageConcurrent('n', 3, [], self.ctx)
        self.assertEqual(rts(), rts_exp('n',(MAX,4,1,0)))
        self.assertEqual(rrts(), rrts_exp('n',(1,4,MAX)))
        self.assertEqual(trs(), tr_exp('n', ((4,MAX),(1,4),(0,1))))
        # 0:t2 (Write to RTS)
        self.assertEqual(t2.next(), (0,-2))
        self.assertEqual(rts(), rts_exp('n', (MAX,4,2,1,0)))
        # 0:t3 (Write to RTS)
        self.assertEqual(t3.next(), (0,-3))
        self.assertEqual(rts(), rts_exp('n', (MAX,4,3,2,1,0)))
        # 1:t2 (Write to RRTS)
        self.assertEqual(t2.next(), (1,2))
        self.assertEqual(rrts(), rrts_exp('n',(1,2,4,MAX)))
        # 1:t3 (Write to RRTS)
        self.assertEqual(t3.next(), (1,3))
        self.assertEqual(rrts(), rrts_exp('n',(1,2,3,4,MAX)))
        # 2 (Scan RTS for precedent)
        self.assertEqual(t2.next(), (2,1))
        self.assertEqual(t3.next(), (2,2))
        # 4 (Scan RRTS for subsequent)
        self.assertEqual(t2.next(), (4,3))
        self.assertEqual(t3.next(), (4,4))
        # 7:t2 (Insert transition - incoming)
        self.assertEqual(t2.next(), (7,(-1,-2)))
        self.assertEqual(trs(), tr_exp('n', ((4,MAX),(1,4),(1,2),(0,1))))
        # 7:t3 (Insert transition - incoming)
        self.assertEqual(t3.next(), (7,(-2,-3)))
        self.assertEqual(trs(), tr_exp('n', ((4,MAX),(2,3),(1,4),(1,2),(0,1))))
        # 7:t2 (Insert transition - outgoing)
        self.assertEqual(t2.next(), (7,(-2,-3)))
        self.assertEqual(trs(), tr_exp('n', ((4,MAX),(2,3),(1,4),(1,2),(0,1))))
        # 7:t3 (Insert transition - outgoing)
        self.assertEqual(t3.next(), (7,(-3,-4)))
        self.assertEqual(trs(), tr_exp('n', ((4,MAX),(3,4),(2,3),(1,4),(1,2),(0,1))))
        # 10:t2 (Delete Transition)
        self.assertEqual(t2.next(), (10,(-1,-3)))
        self.assertEqual(trs(), tr_exp('n', ((4,MAX),(3,4),(2,3),(1,4),(1,2),(0,1))))
        # 10:t3 (Delete Transition)
        self.assertEqual(t3.next(), (10,(-2,-4)))
        self.assertEqual(trs(), tr_exp('n', ((4,MAX),(3,4),(2,3),(1,4),(1,2),(0,1))))
        # 8 (Scan RTS)
        self.assertEqual(t2.next(), (8,(-3,-1,[-3,-2,-1])))
        self.assertEqual(t3.next(), (8,(-4,-2,[-4,-3,-2])))
        # 9 (Scan Transition)
        self.assertEqual(t2.next(), (9,(-2,-1,[(-2,-3),(-1,-4),(-1,-2)])))
        self.assertEqual(t3.next(), (9,(-3,-2,[(-3,-4),(-2,-3)])))
        # 10:t2 (Delete Transition)
        self.assertEqual(t2.next(), (10,(-1,-4)))
        self.assertEqual(trs(), tr_exp('n', ((4,MAX),(3,4),(2,3),(1,2),(0,1))))
        # 8 (Scan RTS)
        self.assertEqual(t2.next(), (8,(-3,-1,[-3,-2,-1])))
        # 9 (Scan Transition)
        self.assertEqual(t2.next(), (9,(-2,-1,[(-2,-3),(-1,-2)])))
        # 11 (Done)
        with self.assertRaises(StopIteration): t2.next()
        with self.assertRaises(StopIteration): t3.next()
        self.assertEqual(rts(), rts_exp('n', (MAX,4,3,2,1,0)))
        self.assertEqual(rrts(), rrts_exp('n',(1,2,3,4,MAX)))
        self.assertEqual(trs(), tr_exp('n', ((4,MAX),(3,4),(2,3),(1,2),(0,1))))

