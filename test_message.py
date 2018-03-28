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
        # 8 (Scan RTS)
        self.assertEqual(t2.next(), (8,9,(-3,-1,[-3,-2,-1])))
        # 9 (Scan Transition)
        self.assertEqual(t2.next(), (9,10,(-2,-1,[(-2,-3),(-1,-2)])))
        # 11 (Done)
        with self.assertRaises(StopIteration): t2.next()
        with self.assertRaises(StopIteration): t3.next()
        self.assertEqual(rts(), rts_exp('n', (MAX,4,3,2,1,0)))
        self.assertEqual(rrts(), rrts_exp('n',(1,2,3,4,MAX)))
        self.assertEqual(trs(), tr_exp('n', ((4,MAX),(3,4),(2,3),(1,2),(0,1))))

class NotTerminatedException (AssertionError):
    pass


class MyTestsMeta(type):
    def __new__(cls, name, bases, attrs):
        if True:
            nThreads = 2
            for line in open('input.txt', 'r'):
                line = line.strip()
                name = "test_"+line
                attrs[name] = cls.gen(nThreads, [int(i) for i in line])
        else:
            tests = ['1000011110111100000']
            tests = ['0'*11]
            for t in tests:
                name = "test_"+t
                attrs[name] = cls.gen(2, [int(i) for i in t])
        return super(MyTestsMeta, cls).__new__(cls, name, bases, attrs)

    @classmethod
    def gen(cls, n, order):
        s = ''.join(str(i) for i in order)
        def fn(self):
            try:
                i = self.doit(n, order)
            except NotTerminatedException as e:
                for i in e.args[0]:
                    print >> MyTests.todo, s+str(i)
                raise
            except AssertionError:
                print >> MyTests.failed, s
                raise
            else:
                print >> MyTests.passed, s
        return fn



class MyTests(unittest.TestCase):
    __metaclass__ = MyTestsMeta

    failed = open('failed.txt', 'w')
    todo = open('todo.txt', 'w')
    passed = open('passed.txt', 'w')

    def printAction(self, thread, result):
        rts,tr = '',''
        if result[0] == 0:
            rts = ''.join(str(-i) for i in sorted (j.time for j in self.ctx.RTS._table.iterkeys()))
        if result[0] in (7,10):
            tr = ','.join(str(-i)+str(-j) for i,j in sorted ((k[1],k[2]) for k in self.ctx.Transitions._table.iterkeys()))
        print '{rts:<8}{tr:<18}'.format(rts=rts, tr=tr),
        print ' ' * (8*thread) , '%d:%s'% (result[0], self.printAction.format[result[0]](result[2]))
    printAction.format = {
        0: lambda x: "RTS<-{}".format(-x),
        1: lambda x: "RRTS<-{}".format(x),
        2: lambda x: "u={}".format(x),
        3: lambda x: "",
        4: lambda x: "s={}".format(x),
        5: lambda x: "",
        6: lambda x: "",
        7: lambda x: "TR<-{}{}".format(-x[0],-x[1]),
        8: lambda x: "m={}".format(''.join(str(-i) for i in x[2])),
        9: lambda x: "t={}".format(','.join(str(-i)+str(-j) for i,j in x[2])),
        10:lambda x: "TR<-({}{})".format(-x[0],-x[1])
        }

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
                try: 
                    result = threads[i].next()
                except StopIteration: 
                    threads[i] = None
                else:
                    self.printAction(i, result)

        # Give each thread a chance to drain.  If more than one thread remain
        # active after this, then we did not terminate
        running, results = [],[]
        for i,t in enumerate(threads):
            if t:
                try:
                    result = t.next()
                except StopIteration:
                    pass
                else:
                    running.append((i,t))
                    results.append((i,result))

        # If more than one thread remain active, we did not terminate
        if len(running) > 1:
            raise NotTerminatedException([i[0] for i in running])

        # Print the single result (if any) from the drain
        for i,r in results:
            self.printAction(i, r)

        # Complete the drain on the running thread (if one exists)
        for i,t in running:
            while True:
                try: 
                    result = t.next()
                except StopIteration: 
                    break
                else:
                    self.printAction(i, result)

        msgs = [MAX] + range(threadCnt+1,-1,-1)
        self.assertEqual(self.ctx.RTS.prefix('n'), 
                rts_exp('n', msgs))
        self.assertEqual(self.ctx.RRTS.prefix('n'), 
                rrts_exp('n', msgs[-2::-1]))
        trs =[(i,j) for i,j in zip(msgs[1:],msgs[:-1])] 
        self.assertEqual(self.ctx.Transitions.prefix('n'), 
                tr_exp('n', trs))
