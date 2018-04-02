#! /usr/bin/env python

from collections import namedtuple
from itertools import chain
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
    RTS.insert((n,-t), x)
    yield 0, -t

    RRTS.insert((n,t), 0)
    yield 1, t

    # Find preceding message
    try:
        prev = RTS.scan((n,-t), (n+'\0', 0))[1]
        yield 2, -prev[0].time
    except IndexError:
        # No preceding message.  Insert one at time 0
        u,y = 0, []
        RTS.insert((n,u), y)
        yield 3, None
    else:
        u,y = prev[0].time, prev[1]

    # Find subsequent message
    try:
        following = RRTS.scan((n,t), (n+'\0', 0))[1]
        yield 4, following[0].time
    except IndexError:
        # No subsequent message.  Insert one at time MAX
        s = MAXINT
        RTS.insert((n,-s), [])
        yield 5, None
        RRTS.insert((n,s), 0)
        yield 6, None
    else:
        s = following[0].time
    s = -s

    # Set up preconditions to loop
    #  Precondition: No transitions are known to us
    transitions = []
    #  Precondition: Assume an edge u-s and mark it for delete, even though
    #   we haven't seen it in the Transition table.  This optimizes for the
    #   common case in which messages per node are processed one-at-a-time
    #   at the expense of messages processed simulataneously.
    to_delete = [(n,u,s)]
    while True:
	# Determine transitions to insert
        expected = ((n,u,-t), (n,-t,s))
        to_insert = [i for i in expected if i not in transitions]
        if not to_insert and not to_delete:
            break

        # Insert transitions to adjacent messages
        for i in to_insert:
            Transitions.insert(i,None)
            yield 7, i[1:]

	# Delete transitions known to be invalid
        for i in to_delete:
            Transitions.delete(i)
            yield 10, i[1:]

        # Get relevant messages and transitions
        messages = RTS.scan((n,s),(n,u), True)
        yield 8, (s,u,[i[0].time for i in messages])
        transitions = [i[0] for i in Transitions.scan((n,-t,-MAXINT),(n,u,MAXINT))]
        yield 9, (-t,u, [i[1:] for i in transitions])

        # Get all of the times that we know about, either via messages or
        #  transitions.
        times = sorted(set(i for i in chain (
            (i[0].time for i in messages),
            (i.precedent for i in transitions),
            (i.subsequent for i in transitions))))

        # Delete transitions
        #  We need to ensure that there are no transitions with the same precedent.
        #  If any exist, delete all transitions excepting the adjacent subsequent.
        #  This is correct because if this thread are responsible for an extra
        #  transition, then the precedent of that edge must be either t or u (since
        #  we added transitions with those precedents).  So we ensure that there
        #  are no duplicates from those
        #TODO: delete all edges except those to the subsequent *time*.  This should
        # let us converge more quickly
        to_delete = []
        for precedent in (-t,u):
            q = [i for i in transitions if i.precedent == precedent]
            for i in q[:-1]:
                to_delete.append(i)

        # Find adjacent messages for generating expected transitions.
        for idx, val in enumerate(times):
            if val == -t:
                u = times[idx+1]
                s = times[idx-1]
                break
        else:
            assert False
