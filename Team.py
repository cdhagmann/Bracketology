# -*- coding: utf-8 -*-
"""
Created on Mon Aug 11 13:04:35 2014

@author: cdhagmann
"""

from Bracket_Functions import clean_pair, clean_school
from Bracket_Functions import Pyth_Range, Teams, num
from Bracket_Functions import id_search, kp_reader, ESPN_Schedule
from Bracket_Functions import Log5

import pickle, re, math, csv, os
from collections import defaultdict

tm = re.compile(r'\(\d+\)')


def valid_team_set(T):
    M = len(T)
    N = round(math.log(M, 2), 3)
    assert int(N) == N, '{} is not a power of 2'.format(M)
    return int(M), int(N)

def default_Pr():
    return [1.0]

class Team():
    def __init__(self, school, year):
        self.school, self.year = clean_pair(school, year)
        self.pair = self.school, self.year
        self.archive = 'PICKLES/{}_{}.pickle'.format(*self.pair)

        if os.path.isfile(self.archive):
            cls = Team.from_file(*self.pair)
            for m in dir(cls):
                if m[0] != '_':
                    setattr(self, m, getattr(cls, m))
        else:
            assert self.school in Teams[self.year], "{} '{}".format(*self.pair)

            self.ID = id_search(*self.pair)
            self.Pyth = kp_reader(*self.pair)[13]

            self.Pr = defaultdict(default_Pr)

            self.depth = {'Actual'                  : 0,
                          ('conditional',    'kNN') : defaultdict(int),
                          ('conditional',    'Rank'): defaultdict(int),
                          ('nonconditional', 'kNN') : defaultdict(int),
                          ('nonconditional', 'Rank'): defaultdict(int)}

            self.TM = {}

            with open('Brackets/{0}/teams_20{0}.csv'.format(self.year), 'rb') as f:
                my_csv = csv.reader(f)
                F = [[clean_school(s, year) for s in line] for line in my_csv]

            for R in zip(*F):
                if self.school in R:
                    self.Rank = R.index(self.school) + 1
                    assert 1 <= self.Rank <= 16
                    break
            else:
                print self.school

            self.depth['Actual'] = 0
            self.opponents, self.matches = [], []

            for row in ESPN_Schedule(*self.pair):
                opp = clean_school(row[1], year)
                if opp is None and tm.search(row[1]) is not None:
                    if self.depth['Actual'] == 0:
                        opp_rank = num.search(row[1]).group()
                        Rank = 17 - int(opp_rank)
                        if Rank != self.Rank:
                            continue

                    if row[2][0] == 'W':
                        self.depth['Actual'] += 1

                elif opp in Teams[self.year]:
                    Adv = 1 if '@' in row[1] else (0 if '*' in row[1] else -1)
                    WL = row[2][0]

                    self.opponents.append(opp)
                    self.matches.append((opp, [Adv, WL]))

            temp = [m[1][1] for m in self.matches]
            self.record = (temp.count('W'), temp.count('L'))
            self.write()

    @classmethod
    def from_file(cls, school, year):
        school, year = clean_pair(school, year)

        archive = 'PICKLES/{}_{}.pickle'.format(school, year)

        if os.path.isfile(archive):
            with open(archive, 'rb') as f:
                cls = pickle.load(f)
                return cls


    def __repr__(self):
        return "{} '{}".format(*self.pair)

    def find_field(self, Teams):
        self.field = []
        self.Teams = Teams
        M, N = valid_team_set(self.Teams)

        seen = set()
        seen.add(self)
        for j in xrange(1, N+1):
            sub_brackets = [self.Teams[i:i + 2 ** (j)] for i in range(0, M, 2 ** (j))]
            for sub_list in sub_brackets:
                if self in sub_list:
                    new_field = [s for s in sub_list if s not in seen]
                    map(seen.add, new_field)
                    self.field.append(new_field)
                    break



    def write(self):
        with open(self.archive, 'wb') as f:
            pickle.dump(self, f, protocol=-1)


    def distance(self, *args):
        if len(args) == 1:
            B = args[0]
            if isinstance(B, Team):
                return abs(self.Pyth - B.Pyth) / Pyth_Range[self.year]
            elif isinstance(B, str):
                BP = float(kp_reader(B, self.year)[13])
                return abs(self.Pyth - BP) / Pyth_Range[self.year]
        else:
            Results = []
            for B in args:
                if isinstance(B, Team):
                    Results.append((B.school, self.distance(B)))
                elif isinstance(B, str):
                    Results.append((B, self.distance(B)))

            Results.sort(key=lambda (b, d): d)
            return Results

    def nearest_neighbor(self, B, Adv=0, k=5, output=False):
        Neigh_B = [(d[1], Ap, B.distance(Ap), d[0]) for Ap, d in self.matches]
        Neigh_B.sort(key=lambda (w, t, d, b): d)
        Neigh_B.sort(key=lambda (w, t, d, b): int(b != Adv))
        Neigh_B = [(w, t, d) for w, t, d, b in Neigh_B]

        if output:
            for tup in Neigh_B:
                print '{}: {:25} {:.4f}'.format(*tup)

        weight = lambda d: (1 - d) ** 1.

        W = sum([weight(d) for w, t, d in Neigh_B[:k] if w == 'W'])
        L = sum([weight(d) for w, t, d in Neigh_B[:k] if w == 'L'])

        return W, L

    def Match(self, B, k=5, match='kNN'):
        assert match in ('kNN', 'Rank')
        if (B.school, k, match) not in self.TM:
            if match == 'kNN':
                WA, LA = self.nearest_neighbor(B, k=k)
                WB, LB = B.nearest_neighbor(self, k=k)

                TA, TB = WA + LA, WB + LB

                p_A = (WA + LB) / (TA + TB)
                p_B = (LA + WB) / (TA + TB)

                P = Log5(p_A, p_B)
            else:
                P = Log5(self.Pyth, B.Pyth)

            self.TM[B.school, k, match] = P
            B.TM[self.school, k, match] = 1 - P
            return P
        else:
            return self.TM[B.school, k, match]
