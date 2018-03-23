#! /usr/bin/env python

from collections import namedtuple
from sys import maxint as MAXINT
from table import TransitionsKey, RTSKey
Context = namedtuple('Context', ('RTS', 'RRTS', 'Transitions'))

MAXINT=9

def onMessage(n,t,x, ctx):
    RTS, RRTS, Transitions = ctx.RTS, ctx.RRTS, ctx.Transitions
    RTS.insert((n,-t), x)
    RRTS.insert((n,t), 0)

    try:
        prev = RTS.scan((n,-t), (n+'\0', 0))[1]
    except IndexError:
        u,y = 0, []
        RTS.insert((n,u), y)
    else:
        u,y = prev[0].time, prev[1]

    try:
        following = RRTS.scan((n,t), (n+'\0', 0))[1]
    except IndexError:
        s = MAXINT
        RTS.insert((n,-s), [])
        RRTS.insert((n,s), 0)
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

        # Get relevant messages and transitions
        messages = RTS.scan((n,s),(n,u), True)
        transitions = [i[0] for i in Transitions.scan((n,-t,-MAXINT),(n,u,MAXINT))]

        # Delete messages
        q = [i for i in transitions if i.precedent == u]
        if q[-1] == (n,u,-t):
            for i in q[:-1]:
                Transitions.delete(i)

        # Find adjacent messages
        for idx, val in enumerate(messages):
            if val[0] == (n,-t):
                u = messages[idx+1][0].time
                s = messages[idx-1][0].time
                break
        else:
            assert False





def onMessageConcurrent(n,t,x, ctx):
    RTS, Transitions = ctx.RTS, ctx.Transitions
    RTS.insert((n,-t), x)
    yield #1

    try:
        prev = RTS.scan((n,-t), (n+'\0', 0))[1]
    except IndexError:
        u,y = 0, []
    else:
        u,y = prev[0].time, prev[1] 
    yield #2

    Transitions.insert((n,u,-t), None)
    yield #3

    transitions = [i[0] for i in Transitions.prefix((n,u))]
    s = min(i.subsequent for i in transitions)
    yield #4

    messages = RTS.scan((n,s), (n,u), True)
    if (u == 0):
        messages.append((RTSKey('n',0),[]))
    expected = [TransitionsKey(n,i[0].time,j[0].time) for i,j in zip(messages[1:], messages[:-1])]
    yield #5

    for t in set(transitions) - set(expected):
        Transitions.delete(t)
    for t in set(expected) - set(transitions):
        Transitions.insert(t, None)
    yield #6
