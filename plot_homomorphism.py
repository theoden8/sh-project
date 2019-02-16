#!/usr/bin/env python3


from graph_utils import *
from homomorphism_solver import *


if __name__ == "__main__":
    plt.switch_backend('agg')
    # G, gname = make_random_graph()
    G = nx.binomial_graph(24, .4)
    print('nodes', len(list(G.nodes())), 'edges', len(list(G.edges())))
    nx.write_gpickle(G, 'graph.pkl')
    G = nx.read_gpickle('graph.pkl')
    H, phi = make_random_homomorphism(G)
    nx.write_gpickle(H, 'graph_morph.pkl')
    H = nx.read_gpickle('graph_morph.pkl')
    no_solns = 0
    solutions = find_homomorphisms(G, H)
    # if len(solutions) > 0:
        # soln = solutions[0]
        # print('homomorphism', soln)
    plot_homomorphism(G, H, 'title', filename='homomorphism.png')
    print(solutions)
