# For given numbers of threads and operations per thread, generate a list of
# all possible operation orderings such that each thread performs the desired
# number of operations.  

from sys import argv

threads = int(argv[1])
iterations = int(argv[2])
slotCount = threads*iterations

def recurse(slots, counts):
    if len(slots) == slotCount:
        print ''.join(str(i) for i in slots)
        return
    for t in range(threads):
        if counts[t] < iterations:
            c = [i for i in counts]
            c[t] += 1
            recurse (slots+[t], c)

recurse([], [0]*threads)


