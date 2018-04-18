#! /usr/bin/env python

from collections import namedtuple
from itertools import chain
from sys import maxint as MAXINT
from table import TransitionsKey, RRTKey
Context = namedtuple('Context', ('RRT', 'RT', 'Transitions'))

MAXINT=9

def onMessage(n,t,x,ctx):
    f = onMessageConcurrent(n,t,x,ctx)
    for _ in f:
        pass

def onMessageConcurrent(n,t,y, ctx):
    RRT, RT, Transitions = ctx.RRT, ctx.RT, ctx.Transitions

    RT.insert((n,t), y)
    yield 1, t

    RRT.insert((n,-t), y)
    yield 0, -t

    # Find preceding message
    try:
        prev = RRT.scan((n,-t), (n+'\0', 0))[1]
        yield 2, (-t, -prev[0].time)
    except IndexError:
        # No preceding message.  Insert one at time 0
        s,x = 0, []
        RRT.insert((n,-s), x)
        yield 3, None
        RT.insert((n,s), x)
        yield 5, None
    else:
        s,x = -prev[0].time, prev[1]

    # Find subsequent message
    try:
        following = RT.scan((n,t), (n+'\0', 0))[1]
        yield 4, (t, following[0].time)
    except IndexError:
        # No subsequent message.  Insert one at time MAX
        u,z = MAXINT, []
        RT.insert((n,u), z)
        yield 6, None
    else:
        u,z = following[0].time, following[1] 

    # Set up preconditions to loop
    #  Precondition: No transitions are known to us
    transitions = []
    #  Precondition: Assume an edge u-s and mark it for delete, even though
    #   we haven't seen it in the Transition table.  This optimizes for the
    #   common case in which messages per node are processed one-at-a-time
    #   at the expense of messages processed simulataneously.
    to_delete = [(n,s,u)]
    while True:
	# Determine transitions to insert
        expected = ((n,s,t), (n,t,u))
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
        messages = RT.scan((n,s),(n,u), True)
        yield 8, (s,u,[i[0].time for i in messages])
        transitions = [i[0] for i in Transitions.scan((n,s,0),(n,t,MAXINT),True)]
        yield 9, (s,t, [i[1:] for i in transitions])

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
        for precedent in (t,s):
            q = [i for i in transitions if i.precedent == precedent]
            for i in q[1:]:
                to_delete.append(i)

        # Find adjacent messages for generating expected transitions.
        t_index = times.index(t)
        s = times[t_index - 1]
        u = times[t_index + 1]
