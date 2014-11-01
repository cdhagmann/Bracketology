"""
Run the code for the years 2003 - 2014 in parallel.
"""


from Bracket_Class import Bracket, clean_year
import multiprocessing as mp
import time


def parallel_bracket(bracket_year):
    """
    Bundles commands together for passing to mp
    """
    bracket_instance = Bracket(bracket_year)
    bracket_instance.run()
    bracket_instance.write_to_csv()
    bracket_instance.write()


def p_print(num, label):
    """
    Prints time well
    """
    if num == 0:
        return ''
    elif num == 1:
        return '{} {} '.format(num, label)
    else:
        return '{} {}s '.format(num, label)


def htime(seconds):
    """
    Prints time in easy to process string
    """
    hours, i = divmod(seconds, 3600)
    minutes, seconds = divmod(i, 60)
    seconds = int(seconds)

    return ''.join((p_print(hours, 'hour'),
                    p_print(minutes, 'minute'),
                    p_print(seconds, 'second')))


if __name__ == '__main__':
    print time.ctime()
    START = time.time()

    PROCESSES = []
    for year in (clean_year(y) for y in range(3, 15)):
        PROCESSES.append(mp.Process(target=parallel_bracket, args=(year,)))

    for p in PROCESSES:
        p.start()

    for p in PROCESSES:
        p.join()

    B = {}
    for year in (clean_year(y) for y in range(3, 15)):
        B[year] = Bracket.from_file(year)

    print time.ctime()
    END = time.time()
    print 'Finished in {}!'.format(htime(END - START))
