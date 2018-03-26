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
        self.assertEqual(t2.next(), (0,0,-2))
        self.assertEqual(rts(), rts_exp('n', (MAX,4,2,1,0)))
        # 0:t3 (Write to RTS)
        self.assertEqual(t3.next(), (0,0,-3))
        self.assertEqual(rts(), rts_exp('n', (MAX,4,3,2,1,0)))
        # 1:t2 (Write to RRTS)
        self.assertEqual(t2.next(), (1,1,2))
        self.assertEqual(rrts(), rrts_exp('n',(1,2,4,MAX)))
        # 1:t3 (Write to RRTS)
        self.assertEqual(t3.next(), (1,1,3))
        self.assertEqual(rrts(), rrts_exp('n',(1,2,3,4,MAX)))
        # 2 (Scan RTS for precedent)
        self.assertEqual(t2.next(), (2,2,1))
        self.assertEqual(t3.next(), (2,2,2))
        # 4 (Scan RRTS for subsequent)
        self.assertEqual(t2.next(), (4,3,3))
        self.assertEqual(t3.next(), (4,3,4))
        # 7:t2 (Insert transition - incoming)
        self.assertEqual(t2.next(), (7,4,(-1,-2)))
        self.assertEqual(trs(), tr_exp('n', ((4,MAX),(1,4),(1,2),(0,1))))
        # 7:t3 (Insert transition - incoming)
        self.assertEqual(t3.next(), (7,4,(-2,-3)))
        self.assertEqual(trs(), tr_exp('n', ((4,MAX),(2,3),(1,4),(1,2),(0,1))))
        # 7:t2 (Insert transition - outgoing)
        self.assertEqual(t2.next(), (7,5,(-2,-3)))
        self.assertEqual(trs(), tr_exp('n', ((4,MAX),(2,3),(1,4),(1,2),(0,1))))
        # 7:t3 (Insert transition - outgoing)
        self.assertEqual(t3.next(), (7,5,(-3,-4)))
        self.assertEqual(trs(), tr_exp('n', ((4,MAX),(3,4),(2,3),(1,4),(1,2),(0,1))))
        # 8 (Scan RTS)
        self.assertEqual(t2.next(), (8,6,(-3,-1,[-3,-2,-1])))
        self.assertEqual(t3.next(), (8,6,(-4,-2,[-4,-3,-2])))
        # 9 (Scan Transition)
        self.assertEqual(t2.next(), (9,7,(-2,-1,[(-2,-3),(-1,-4),(-1,-2)])))
        self.assertEqual(t3.next(), (9,7,(-3,-2,[(-3,-4),(-2,-3)])))
        # 10:t2 (Delete Transition)
        self.assertEqual(t2.next(), (10,8,(-1,-4)))
        self.assertEqual(trs(), tr_exp('n', ((4,MAX),(3,4),(2,3),(1,2),(0,1))))
        # 11 (Done)
        self.assertEqual(t2.next(), (11,9,None))
        self.assertEqual(t3.next(), (11,8,None))
        self.assertEqual(rts(), rts_exp('n', (MAX,4,3,2,1,0)))
        self.assertEqual(rrts(), rrts_exp('n',(1,2,3,4,MAX)))
        self.assertEqual(trs(), tr_exp('n', ((4,MAX),(3,4),(2,3),(1,2),(0,1))))
        with self.assertRaises(StopIteration): t2.next()
        with self.assertRaises(StopIteration): t3.next()

class MyTestsMeta(type):
    def __new__(cls, name, bases, attrs):
        threads =2 
        iterations = 12
        slots = threads*iterations
        for i in range(threads**slots):
            break
            c=[]
            cnt=[0]*threads
            for j in range(slots):
                t = (i/(threads**j))%threads
                cnt[t] += 1
                if cnt[t] > iterations:
                    break
                c.append(t)
            else:
                name = "test_{}-{}".format(threads,''.join(str(i) for i in c))
                attrs[name] = cls.gen(threads, c)
        t='111111100000000001111100'
        name = "test_{}-{}".format(threads,''.join(str(i) for i in t))
        attrs[name] = cls.gen(threads, [int(i) for i in t])



        return super(MyTestsMeta, cls).__new__(cls, name, bases, attrs)

    @classmethod
    def gen(cls, n, order):
        def fn(self):
            self.doit(n, order)
        return fn

class MyTests(unittest.TestCase):
    __metaclass__ = MyTestsMeta
    def setUp(self):
        RTS=Table(RTSKey)
        RRTS=Table(RRTSKey)
        Transitions=Table(TransitionsKey)
        self.ctx = Context(RTS, RRTS, Transitions)

    def doit(self, threadCnt, order):
        onMessage('n', 1, [], self.ctx)
        threads = [onMessageConcurrent('n', 2+i, [], self.ctx) for i in range(threadCnt)]

        for i in order:
            if threads[i]:
                try: print i,threads[i].next()
                except StopIteration: threads[i] = None

        running = [i for i in threads if i]
        self.assertTrue(len(running)<2)

        for i in running:
            while True:
                try: i.next()
                except StopIteration: break

        msgs = [MAX] + range(threadCnt+1,-1,-1)
        self.assertEqual(self.ctx.RTS.prefix('n'), 
                rts_exp('n', msgs))
        self.assertEqual(self.ctx.RRTS.prefix('n'), 
                rrts_exp('n', msgs[-2::-1]))
        trs =[(i,j) for i,j in zip(msgs[1:],msgs[:-1])] 
        self.assertEqual(self.ctx.Transitions.prefix('n'), 
                tr_exp('n', trs))
