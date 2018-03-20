import unittest
from message import onMessage, Context
from table import Table, RTSKey, TransitionsKey


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
        expected = [(('n',i,j),None) for i,j in zip((-2,-1,0), (-3,-2,-1))] 
        self.assertEqual(tr, expected)

    def test_outOfOrder(self):
        onMessage('n', 1, [], self.ctx)
        onMessage('n', 3, [], self.ctx)
        onMessage('n', 2, [], self.ctx)
        rts = self.ctx.RTS.prefix('n')
        tr = self.ctx.Transitions.prefix('n')
        expected = [(('n', i),[]) for i in range (-3,0)]
        self.assertEqual(rts, expected)
        expected = [(('n',i,j),None) for i,j in zip((-2,-1,0), (-3,-2,-1))] 
        self.assertEqual(tr, expected)
