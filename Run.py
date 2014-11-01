from Bracket_Class import Bracket, clean_year
import multiprocessing as mp
import time


def parallel_bracket(year):
    B = Bracket(year)
    B.run()
    B.write_to_csv()
    B.write()


def p_print(n, label):
    if n == 0:
        return ''
    elif n == 1:
        return '{} {} '.format(n, label)
    else:
        return '{} {}s '.format(n, label)


def htime(s):
    H, i = divmod(s, 3600)
    M, S = divmod(i, 60)
    S = int(S)

    return p_print(H, 'hour') + p_print(M, 'minute') + p_print(S, 'second')


if __name__ == '__main__':
    print time.ctime()
    t1 = time.time()

    processes = []
    for year in (clean_year(y) for y in range(3, 15)):
        processes.append(mp.Process(target=parallel_bracket, args=(year,)))

    for p in processes:
        p.start()

    for p in processes:
        p.join()

    B = {}
    for year in (clean_year(y) for y in range(3, 15)):
        B[year] = Bracket.from_file(year)

    print time.ctime()
    t2 = time.time()
    print 'Finished in {}!'.format(htime(t2 - t1))
