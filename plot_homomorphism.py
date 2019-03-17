#!/usr/bin/env python3


import sys

from graph_utils import *
from homomorphism_solver import *


if __name__ == "__main__":
    plt.switch_backend('agg')
    gfile, hfile = sys.argv[1], sys.argv[2]
    G, H = load_graph(gfile), load_graph(hfile)
    phi = is_homomorphic(G, H)
    plot_homomorphism(G, H, phi, filename='homomorphism.png')
