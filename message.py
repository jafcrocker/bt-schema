#! /usr/bin/env python

from collections import namedtuple
from table import TransitionsKey
Context = namedtuple('Context', ('RTS', 'Transitions'))

def onMessage(n,t,x, ctx):
    RTS, Transitions = ctx.RTS, ctx.Transitions
    RTS.insert((n,-t), x)
    try:
        prev = RTS.scan((n,-t), (n+'\0', 0))[1]
    except IndexError:
        u,y = 0, []
    else:
        u,y = prev[0].time, prev[1] 
    Transitions.insert((n,u,-t), None)
    transitions = [i[0] for i in Transitions.prefix((n,u))]
    if len(transitions) == 1:
        return
    s = min(i.subsequent for i in transitions)
    messages = RTS.scan((n,s), (n,u), True)
    if (u == 0):
        messages.append((RTSKey('n',0),[]))
    expected = [TransitionsKey(n,i[0].time,j[0].time) for i,j in zip(messages[1:], messages[:-1])]
    for t in set(transitions) - set(expected):
        Transitions.delete(t)
    for t in set(expected) - set(transitions):
        Transitions.insert(t, None)
