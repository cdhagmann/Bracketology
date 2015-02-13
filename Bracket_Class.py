from Team import Team
import pickle, os, csv, math
from Bracket_Functions import clean_year

class Bracket(object):
    def __init__(self, year):
        self.year = clean_year(year)
        self.archive = 'PICKLES/bracket_{}.pickle'.format(self.year)

        if False:#os.path.isfile(self.archive):
            cls = Bracket.from_file(self.year)
            for m in dir(cls):
                if m[0] != '_':
                    setattr(self, m, getattr(cls, m))
            return None
        else:
            filename = 'Brackets/{0}/teams_20{0}.txt'.format(self.year)
            with open(filename, 'r') as f:
                self.Bracket = [Team(t.strip(), year) for t in f]

            self.M, self.N = self.validate_team_set()
            self.max_k = int(min([len(t.matches) for t in self.Bracket])) + 1
            for t in self.Bracket:
                t.find_field(self.Bracket)

            #self.write()

    def run(self):
        for k in xrange(3, self.max_k):
            count = 1
            for i, A in enumerate(self.Bracket, 1):
                for B in self.Bracket[i:]:
                    info = (A.school, B.school, count, k, self.year)
                    string = '{:25} vs. {:25} ({:4} of 2016) [k = {:2}, year = 20{}]'
                    print string.format(*info)

                    A.Match(B, k, match='kNN')
                    A.Match(B, k, match='Rank')

                    count += 1

        for t in self.Bracket:
            for k in range(3, self.max_k):
                for depth_type in ('conditional', 'nonconditional'):
                    for match in ('kNN', 'Rank'):
                        t.depth[depth_type, match][k] = 0



        for k in range(3, self.max_k):
            for match in ('kNN', 'Rank'):
                self.Method_1(k, match)
                self.Method_2(k, match)


        self.write()

    def __repr__(self):
        return '30{} Bracket'.format(self.year)


    @classmethod
    def from_file(cls, year):
        year = clean_year(year)
        archive = 'PICKLES/bracket_{}.pickle'.format(year)

        if os.path.isfile(archive):
            with open(archive, 'rb') as f:
                cls = pickle.load(f)
                return cls

    def write(self):
        with open(self.archive, 'wb') as f:
            pickle.dump(self, f, protocol=-1)

    def write_to_csv(self):
        RMD = 'DATA/{0}/raw_match_data.csv'.format(self.year)
        RAD = 'DATA/{0}/raw_accuracy_data.csv'.format(self.year)
        AD = 'DATA/{0}/accuracy_data.csv'.format(self.year)

        with open(RMD, 'wb') as f, open(RAD, 'wb') as g, open(AD, 'wb') as h:
            match_writer = csv.writer(f)
            accuracy_writer = csv.writer(g)
            AD_writer = csv.writer(h)
            match_writer.writerow( ('year','k','A','B','kNN','Rank') )
            accuracy_writer.writerow( ('year', 'k', 'A', 'Actual', 'Pred_Ck', 'Pred_NCk', 'Pred_CR', 'Pred_NCR') )
            AD_writer.writerow( ('year', 'k', 'Accuracy_Ck', 'Accuracy_NCk', 'Accuracy_CR', 'Accuracy_NCR', 'Delta_Ck', 'Delta_NCk') )
            for k in xrange(3, self.max_k):
                match_info = lambda A, B: (self.year,
                                           k,
                                           A.school,
                                           B.school,
                                           A.TM[B.school, k, 'kNN'],
                                           A.TM[B.school, k, 'Rank'])

                AD_data = (self.year,
                           k,
                           self.bracket_accuracy(k,'conditional',    'kNN'),
                           self.bracket_accuracy(k,'nonconditional', 'kNN'),
                           self.bracket_accuracy(k,'conditional',    'Rank'),
                           self.bracket_accuracy(k,'nonconditional', 'Rank'),
			   self.bracket_accuracy(k,'conditional',    'kNN') - self.bracket_accuracy(k,'conditional',    'Rank'),
			   self.bracket_accuracy(k,'nonconditional', 'kNN') - self.bracket_accuracy(k,'nonconditional', 'Rank'))

                AD_writer.writerow( AD_data )

                for i, A in enumerate(self.Bracket, 1):
                    accuracy_data = (self.year,
                                     k,
                                     A.school,
                                     A.depth['Actual'],
                                     A.depth['conditional',    'kNN' ][k],
                                     A.depth['nonconditional', 'kNN' ][k],
                                     A.depth['conditional',    'Rank'][k],
                                     A.depth['nonconditional', 'Rank'][k])

                    accuracy_writer.writerow( accuracy_data )
                    for B in self.Bracket[i:]:
                        match_writer.writerow( match_info(A, B) )
                        match_writer.writerow( match_info(B, A) )

    def validate_team_set(self):
        M = len(self.Bracket)
        N = round(math.log(M, 2), 3)
        assert int(N) == N, '{} is not a power of 2'.format(M)
        return int(M), int(N)


    def Method_1(self, k, match='kNN'):
        assert match in ('kNN', 'Rank')

        for d in xrange(self.N):
            for A in self.Bracket:
                new_Pr = sum(B.Pr[k,match][d] * A.TM[B.school, k, match] for B in A.field[d])
                A.Pr[k,match].append( A.Pr[k,match][d] * new_Pr )

        for j in xrange(1, self.N + 1):
            field = [self.Bracket[i:i + 2 ** (j)] for i in range(0, self.M, 2 ** (j))]
            for sub_bracket in field:
                P = [A for A in sub_bracket if A.depth['conditional', match][k] == j - 1]
                P.sort(key=lambda A: A.Pr[k,match][j], reverse=True)
                P[0].depth['conditional', match][k] += 1


    def chalk(self):
        match, k = 'Chalk', 5

        for d in xrange(self.N):
            for A in self.Bracket:
                if A.depth['nonconditional', match][k] == d:
                    B = [B for B in A.field[d] if B.depth['nonconditional', match][k] == d]
                    assert len(B) <= 1
                    if B:
                        B = B[0]
                        P = A.Match(B, match='Rank')
                        if A.Rank < B.Rank:
                            A.depth['nonconditional', match][k] += 1
                        elif A.Rank > B.Rank:
                            B.depth['nonconditional', match][k] += 1
                        else:
                            if P > .5:
                                A.depth['nonconditional', match][k] += 1
                            else:
                                B.depth['nonconditional', match][k] += 1

        return  self.bracket_accuracy(k,'nonconditional',    'Chalk')

    def Method_2(self, k, match='kNN'):
        assert match in ('kNN', 'Rank')

        for d in xrange(self.N):
            for A in self.Bracket:
                if A.depth['nonconditional', match][k] == d:
                    B = [B for B in A.field[d] if B.depth['nonconditional', match][k] == d]
                    assert len(B) <= 1
                    if B:
                        B = B[0]
                        P = A.TM[B.school, k, match]
                        if P > .5:
                            A.depth['nonconditional', match][k] += 1
                        else:
                            B.depth['nonconditional', match][k] += 1

    def pprint(self, k, depth_type='conditional', match='kNN'):
        for t in self.Bracket:
            print '{0:20} {1:3}'.format(t.school, t.depth[depth_type, match][k])



    def bracket_accuracy(self, k, depth_type='conditional', match='kNN', output=False):
        assert depth_type in ('conditional', 'nonconditional')
        assert match in ('kNN', 'Rank', 'Chalk')

        Diff = sum( abs(t.depth[depth_type, match][k] - t.depth['Actual']) for t in self.Bracket)
        Correct = (63 - (Diff / 2.) )

        if output:
            print '{1} Games Correct [{0:.2%}]'.format(Correct / 63., Correct)

        return Correct

    def bracket_score(self):
        score = sum(t.Rank * t.depth['Actual'] for t in self.Bracket)
        assert score >= 203, '{} is not a possible score'.format(score)
        return score

    def bracket_errors(self, k, depth_type='conditional', match='kNN'):
        D = lambda t: (t.school, t.depth[depth_type, match][k] - t.depth['Actual'], t.depth[depth_type, match][k], t.depth['Actual'])
        Diff = filter(lambda tup: tup[1] != 0, map(D, self.Bracket))
        Diff.sort(key=lambda tup: tup[1], reverse=True)

        for info in Diff:
                print '{0:20} {1:3}\t{2:1}\t{3:1}'.format(*info)

        return True
