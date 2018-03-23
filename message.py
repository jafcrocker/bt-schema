#! /usr/bin/env python

from collections import namedtuple
from sys import maxint as MAXINT
from table import TransitionsKey, RTSKey
Context = namedtuple('Context', ('RTS', 'RRTS', 'Transitions'))

MAXINT=9

def onMessage(n,t,x,ctx):
    f = onMessageConcurrent(n,t,x,ctx)
    for _ in f:
        pass

def onMessageConcurrent(n,t,x, ctx):
    RTS, RRTS, Transitions = ctx.RTS, ctx.RRTS, ctx.Transitions
    sequence = 0
    RTS.insert((n,-t), x)
    yield 0, sequence, -t ; sequence += 1

    RRTS.insert((n,t), 0)
    yield 1, sequence, t ; sequence += 1

    try:
        prev = RTS.scan((n,-t), (n+'\0', 0))[1]
        yield 2, sequence, -prev[0].time ; sequence += 1
    except IndexError:
        u,y = 0, []
        RTS.insert((n,u), y)
        yield 3, sequence, None ; sequence += 1
    else:
        u,y = prev[0].time, prev[1]

    try:
        following = RRTS.scan((n,t), (n+'\0', 0))[1]
        yield 4, sequence, following[0].time; sequence += 1
    except IndexError:
        s = MAXINT
        RTS.insert((n,-s), [])
        yield 5, sequence, None; sequence += 1
        RRTS.insert((n,s), 0)
        yield 6, sequence, None ; sequence += 1
    else:
        s = following[0].time
    s = -s

    transitions = []
    while True:
        # Insert transitions to adjacent messages 
        expected = ((n,u,-t), (n,-t,s))
        to_insert = [i for i in expected if i not in transitions]
        if not to_insert:
            break
        for i in to_insert:
            Transitions.insert(i,None)
            yield 7, sequence, i[1:] ; sequence += 1

        # Get relevant messages and transitions
        messages = RTS.scan((n,s),(n,u), True)
        yield 8, sequence, (s,u,[i[0].time for i in messages]) ; sequence += 1
        transitions = [i[0] for i in Transitions.scan((n,-t,-MAXINT),(n,u,MAXINT))]
        yield 9, sequence, (-t,u, [i[1:] for i in transitions]); sequence += 1

        # Delete messages
        q = [i for i in transitions if i.precedent == u]
        if q[-1] == (n,u,-t):
            for i in q[:-1]:
                Transitions.delete(i)
                yield 10, sequence, i[1:] ; sequence += 1

        # Find adjacent messages
        for idx, val in enumerate(messages):
            if val[0] == (n,-t):
                u = messages[idx+1][0].time
                s = messages[idx-1][0].time
                break
        else:
            assert False
    yield 11, sequence, None
