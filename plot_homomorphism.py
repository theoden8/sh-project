#!/usr/bin/env python3


from graph_utils import *
from homomorphism_solver import *


if __name__ == "__main__":
    plt.switch_backend('agg')
    # G, gname = make_random_graph()
    # G = nx.binomial_graph(7, .4)
    # nx.write_gpickle(G, 'graph.pkl')
    G = nx.read_gpickle('graph.pkl')
    # H, phi = make_random_homomorphism(G)
    # nx.write_gpickle(H, 'graph_morph.pkl')
    H = nx.read_gpickle('graph_morph.pkl')
    for soln in is_homomorphism(G, H):
        morph = soln
        print('homomorphism', soln)
        plot_homomorphism(G, H, morph, filename='homomorphism.png')
        break
