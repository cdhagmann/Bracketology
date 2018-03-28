# -*- coding: utf-8 -*-
"""
Created on Fri Oct 31 23:05:09 2014

@author: cdhagmann
"""

import glob
import os


def pickle_cleanse():
    for archive in glob.iglob('DATA/*/*'):
        os.remove(archive)

    for archive in glob.iglob('PICKLES/*'):
        os.remove(archive)


if __name__ == '__main__':
    pickle_cleanse()
