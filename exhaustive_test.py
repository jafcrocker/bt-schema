import unittest
from message import onMessage, onMessageConcurrent, Context, MAXINT as MAX
from table import Table, RRTKey, TransitionsKey, RTKey

rts_exp = lambda x,y: [(RRTKey(x,-i),[]) for i in y]
rrts_exp = lambda x,y: [(RTKey(x,i),0) for i in y]
tr_exp = lambda x,y: [(TransitionsKey(x,-i,-j),None) for i,j in y]
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
            tests = ['0'*9, '1'*9] 
	    tests = ['11100000000011111100000110']
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
            rts = ''.join(str(-i) for i in sorted (j.time for j in self.ctx.RRT._table.iterkeys()))
        if result[0] in (7,10):
            tr = ','.join(str(-i)+str(-j) for i,j in sorted ((k[1],k[2]) for k in self.ctx.Transitions._table.iterkeys()))
        print '{rts:<8}{tr:<18}'.format(rts=rts, tr=tr),
        print ' ' * (8*thread) , '%d:%s'% (result[0], self.printAction.format[result[0]](result[1]))
    printAction.format = {
        0: lambda x: "RRT<-{}".format(-x),
        1: lambda x: "RT<-{}".format(x),
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
        RRT=Table(RRTKey)
        RT=Table(RTKey)
        Transitions=Table(TransitionsKey)
        self.ctx = Context(RRT, RT, Transitions)

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
        self.assertEqual(self.ctx.RRT.prefix('n'), 
                rts_exp('n', msgs))
        self.assertEqual(self.ctx.RT.prefix('n'), 
                rrts_exp('n', msgs[-2::-1]))
        trs =[(i,j) for i,j in zip(msgs[1:],msgs[:-1])] 
        self.assertEqual(self.ctx.Transitions.prefix('n'), 
                tr_exp('n', trs))

if __name__ == '__main__':
    unittest.main(buffer=True)
