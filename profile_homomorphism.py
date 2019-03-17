#!/usr/bin/env python3


import sys
from pycallgraph import PyCallGraph
from pycallgraph.output import GraphvizOutput
import pstats
import cProfile
import pyximport

from graph_utils import *

pyximport.install()

from homomorphism_solver import *


if __name__ == '__main__':
    gfile, hfile = sys.argv[1], sys.argv[2]
    G, H = load_graph(gfile), load_graph(hfile)
    phi = None
    with PyCallGraph(output=GraphvizOutput()):
        phi = is_homomorphic(G, H)
    cProfile.runctx("is_homomorphic(G, H)", globals(), locals(), 'pyprofile.prof')
    s = pstats.Stats('pyprofile.prof')
    s.strip_dirs().sort_stats('time').print_stats()
    print('fail' if phi is None else phi)
