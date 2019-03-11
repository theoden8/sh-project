#!/usr/bin/env python3


import sys

from graph_utils import *
from homomorphism_solver import *


if __name__ == '__main__':
    gfile, hfile = sys.argv[1], sys.argv[2]
    G, H = None, None
    with open(gfile, 'r') as f:
        G = deserialize_graph(f.read())
    with open(hfile, 'r') as f:
        H = deserialize_graph(f.read())
    phi = is_homomorphic(G, H)
    print('fail' if phi is None else phi)
