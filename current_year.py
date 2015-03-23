from Bracket_Class import Bracket, clean_year
import multiprocessing as mp
from collections import defaultdict
import time


def print_bracket(B, k, depth_type='conditional', match='kNN'):
    for depth in xrange(6):
        for t in B.Bracket:
            if t.depth[depth_type, match][k] > depth:
                print t.school
        print     


if __name__ == '__main__':
    B = Bracket(2015)
    ks = (5, 8, 14, 24, B.max_k)

    processes = []
    for k in ks:
        for i, a in enumerate(B.Bracket, 1):
            for b in B.Bracket[i:]:
                processes.append( mp.Process(target=a.Match, args=(b, k), kwargs={'match':'kNN'}) )

    for p in processes:
        p.start()

    for p in processes:
        p.join()

    for t in B.Bracket:
        t.depth['conditional', 'kNN'] = defaultdict(int)

    for k in ks:
        print 'K = ', k
        B.Method_1(k, 'kNN')
        print_bracket(B, k)
