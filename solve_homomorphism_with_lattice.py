#!/usr/bin/env python3


import sys

from graph_utils import *
from lattice_utils import *
from homomorphism_solver import *


if __name__ == '__main__':
    gfile, hfile = sys.argv[1], sys.argv[2]
    lattice = Lattice.load('lattice.json')
    result = lattice.is_homomorphic(gfile, hfile)
    print('YES' if result else 'NO')
