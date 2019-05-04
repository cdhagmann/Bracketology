# -*- coding: utf-8 -*-
"""
Created on Sat Jul 26 2014

@author: cdhagmann
"""

############################################################################
# IMPORT MODULES
############################################################################

import csv
import re
import os
import sys
import pandas
from bs4 import BeautifulSoup
from urllib.request import urlopen


############################################################################
# DEFINE "HELPER" PARAMETERS
############################################################################


class Printer():
    def __init__(self, data):
        sys.stdout.write("\r\x1b[K"+data.__str__())
        sys.stdout.flush()


def clean_year(year):
    Error_message = '{} not a valid input for clean_year'.format(year)
    if isinstance(year, str):
        if len(year) == 4:
            assert '20' in year, Error_message
            return clean_year(year[2:])
        elif len(year) < 4:
            assert 2 <= int(year) <= 15, Error_message
            return '{:02}'.format(int(year))
        else:
            raise ValueError(Error_message)
    elif isinstance(year, int):
        return clean_year(str(year))
    else:
        raise ValueError(Error_message)


############################################################################
# DEFINE GLOBAL PARAMETERS
############################################################################

Teams, Pyth_Range, Brackets = {}, {}, {}
for year in range(3, 16):
    year = clean_year(year)
    filename = 'Brackets/{0}/summary{0}_pt.csv'.format(year)
    df = pandas.read_csv(filename)

    Teams[year] = list(df.TeamName)
    Pyth_Range[year] = float(max(df.Pythag) - min(df.Pythag))

num = re.compile(r'\d+')


############################################################################
# DEFINE GLOBAL FUNCTIONS
############################################################################


KP_ID = pandas.read_csv('kenPom_ID.csv')
ESPN_ID = pandas.read_csv('ESPN.csv')


def ESPN_to_kenpom(school):
    try:
        SID = int(ESPN_ID[ESPN_ID.Team == school.upper()].ID.values[0])
        School = str(KP_ID[KP_ID.ID == SID].Team.values[0])
        return School
    except:
        return None


def kenpom_to_ESPN(school):
    SID = int(KP_ID[KP_ID.Team == school].ID.values[0])
    School = str(ESPN_ID[ESPN_ID.ID == SID].Team.values[0])
    return School


def clean_school(School, year=2014):
    year = clean_year(year)
    school = School.lstrip('vs#@1234567890 ').rstrip('*1234567890 ;\n')

    if num.search(school) is not None:
        return None
    elif school in Teams[year]:
        return school
    elif ESPN_to_kenpom(school) is not None:
        return ESPN_to_kenpom(school)
    elif 'San Jos' in school:
        return 'San Jose St.'
    else:
        # print("    {0:25} - 20{1}".format(school, year))
        return None


def clean_pair(school, year):
    return clean_school(school, year), clean_year(year)


def kp_reader(school, year):
    school, year = clean_pair(school, year)
    filename = 'Brackets/{0}/summary{0}_pt.csv'.format(year)
    df = pandas.read_csv(filename)
    return df[df.TeamName == school].values[0]


def id_search(school, year):
    school = clean_school(school, year)
    if school is None:
        return None
    elif school in list(KP_ID.Team):
        return int(KP_ID[KP_ID.Team == school].ID.values[0])
    elif school in list(ESPN_ID.Team):
        return int(ESPN_ID[ESPN_ID.Team == school].ID.values[0])
    else:
        A = school.rstrip('.')

        link = 'http://espn.go.com/mens-college-basketball/teams'
        soup = BeautifulSoup(urlopen(link), 'html.parser')

        foo = list(soup.findAll('a', href=True))
        T = [a.getText().encode('utf8') for a in foo]

        if A in T:
            idx = T.index(A)
            ID = int(foo[idx]['href'].split('/')[-2])
            print('From ESPN: {0:25} - {1}'.format(school, ID))
            return ID

        link = 'https://bing.com/?q='
        link += '+'.join(['ESPN', 'mens', 'basketball',
                          '2013-14', 'schedule'] + school.split())
        soup = BeautifulSoup(urlopen(link), 'html.parser')
        for a in soup.findAll('a', href=True):
            # print(a['href'])
            if 'mens-college-basketball' in a['href']:
                url = a['href'].split('/')
                try:
                    ID = int(url[-2])
                    assert ID < 4000
                    print('From Bing: {0:25} - {1}'.format(school, ID))
                    return ID
                except:
                    continue


def ESPN_Schedule(school, year):
    school, year = clean_pair(school, year)
    ID = id_search(school, year)

    try:
        html = 'http://espn.go.com/mens-college-basketball/team/'
        html += 'schedule?id={}&year=20{}'.format(ID, year)

        soup = BeautifulSoup(urlopen(html), 'html.parser')

        table = soup.find('table',
                          attrs={'cellspacing': "1", 'cellpadding': "3", 'class': "tablehead"})
        if table is None:
            raise AttributeError

    except AttributeError:
        print('ID: {} is not valid'.format(ID), end=" ")
        # return False

    table_rows = list(table.find_all('tr'))

    if len(table_rows) < 20:
        print('ID: {} is not valid'.format(ID), end=" ")
        return False

    rows = []
    for count, row in enumerate(table_rows):
        row = [val.text.encode('utf8') for val in row.find_all('td')]
        if count >= 2 and len(row) >= 2:
            rows.append(row)

    return rows


def download_schedule(school, year):
    school, year = clean_pair(school, year)
    rows = [['Opponent',    'Advantage', 'WL', 'School Score',    'Opp Score']]
    for row in ESPN_Schedule(school, year):
        opp = clean_school(row[1], year)
        if opp is None:
            continue

        if '@' in row[1]:
            Adv = 1
        elif '*' in row[1]:
            Adv = 0
        else:
            Adv = -1

        WL = row[2][0]

        score = row[2].strip('WL')
        score = score.split()[0].split('-')
        if len(score) != 2:
            continue
        else:
            score = map(int, score)
        if WL == 'W':
            school_score = max(score)
            opp_score = min(score)
        elif WL == 'L':
            school_score = min(score)
            opp_score = max(score)
        else:
            continue

        output = [opp, Adv, WL, school_score, opp_score]
        rows.append(output)

    with open(filename, 'wb') as f:
        writer = csv.writer(f)
        writer.writerows(row for row in rows if row)

    return os.path.isfile(filename)


def Log5(p_A, p_B):
    '''
    Calculate the estimated probability that team A will win a game,
    based on the true winning percentage of Team A and Team B.

    A few notable properties:
        If p_A == 1, Log5 will always give A a 100% chance of victory
        If p_A == 0, Log5 will always give A a 0% chance of victory
        If p_A == p_B, Log5 will always return a 50% chance of victory for either side
        If p_A == 1/2, Log5 will give A a 1-p_B probability of victory.
    '''
    return (p_A * (1 - p_B)) / (p_A * (1 - p_B) + p_B * (1 - p_A))


def bayesian_update(p1, p2):
    return (p1 * p2) / ((p1 * p2) + ((1 - p1) * (1 - p2)))


def clean_bracket(year):
    year = clean_year(year)
    if Brackets.get(year, None) is None:
        A = [1, 64, 32, 33, 17, 48, 16, 49, 24, 41, 9, 56, 25, 40, 8, 57]
        B = [2, 63, 31, 34, 18, 47, 15, 50, 23, 42, 10, 55, 26, 39, 7, 58]
        C = [3, 62, 30, 35, 19, 46, 14, 51, 22, 43, 11, 54, 27, 38, 6, 59]
        D = [4, 61, 29, 36, 20, 45, 13, 52, 21, 44, 12, 53, 28, 37, 5, 60]

        filename = 'Brackets/{0}/teams_20{0}.csv'.format(year)
        with open(filename, 'rb') as f:
            my_csv = csv.reader(f)
            F = [[s for s in line] for line in my_csv]
        idxs = [0, 15, 7, 8, 4, 11, 3, 12, 5, 10, 2, 13, 6, 9, 1, 14]

        Regions = [[region[i] for i in idxs] for region in zip(*F)]

        Bracket = [None for _ in range(64)]
        for indices, region in zip([A, B, C, D], Regions):
            for i, t in zip(indices, region):
                Bracket[i-1] = t

        idxs = A + D + C + B
        Bracket = [Bracket[i-1] for i in idxs]

        filename = 'Brackets/{0}/teams_20{0}.txt'.format(year)
        with open(filename, 'w') as f:
            for t in Bracket:
                f.write(t + '\n')

        return True
