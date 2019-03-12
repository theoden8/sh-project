#!/usr/bin/env python3


import sys

from graph_utils import *
from homomorphism_solver import *


if __name__ == "__main__":
    plt.switch_backend('agg')
    # G = make_random_graph(45)
    # print('nodes', len(list(G.nodes())), 'edges', len(list(G.edges())))
    # nx.write_gpickle(G, 'graph.pkl')
    # G = nx.read_gpickle('graph.pkl')
    # H, phi = make_random_homomorphism(G)
    # nx.write_gpickle(H, 'graph_morph.pkl')
    # H = nx.read_gpickle('graph_morph.pkl')
    gfile, hfile = sys.argv[1], sys.argv[2]
    G, H = None, None
    with open(gfile, 'r') as f:
        G = deserialize_graph(f.read())
    with open(hfile, 'r') as f:
        H = deserialize_graph(f.read())
    phi = is_homomorphic(G, H)
    plot_homomorphism(G, H, phi, filename='homomorphism.png')
