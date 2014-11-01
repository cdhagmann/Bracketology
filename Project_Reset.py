# -*- coding: utf-8 -*-
"""
Created on Fri Oct 31 23:05:09 2014

@author: cdhagmann
"""

import glob, os

def pickle_cleanse():
    """
    Removes the results files and the .pickle files so that the code can be
    run fresh. This is necessary if you have made changes to the Bracket or
    the Team class.
    """
    for archive in glob.iglob('DATA/*/*'):
        os.remove(archive)

    for archive in glob.iglob('PICKLES/*'):
        os.remove(archive)

if __name__ == '__main__':
    pickle_cleanse()
