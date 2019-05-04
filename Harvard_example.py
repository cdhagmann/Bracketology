from Team import Team
from Bracket_Functions import Log5

H = Team('Harvard', 2014)
C = Team('Cincinnati', 2014)

P_Log5 = Log5(H.Pyth, C.Pyth)
print('Harvard (Log5): {:.2%}'.format(P_Log5))

H.nearest_neighbor(C, k=10)
C.nearest_neighbor(H, k=10)

P_kNN = H.Match(C, k=10)
print('Harvard (kNN): {:.2%}'.format(P_kNN))

WB, LB = C.nearest_neighbor(H, k=10)
WA, LA = H.nearest_neighbor(C, k=10)
TA, TB = WA + LA, WB + LB

p_A = (WA + LB) / (TA + TB)
p_B = (LA + WB) / (TA + TB)

print(p_A, p_B)
