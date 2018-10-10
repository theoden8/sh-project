#!/usr/bin/env python3


import os
import math
from more_itertools import random_permutation

import matplotlib.pyplot as plt
import numpy as np

import networkx as nx
import networkx.generators.classic
import networkx.generators.community
import networkx.generators.random_graphs

from random import random
from random import randint


def save_figure(fig, filename):
    if os.path.exists(filename):
        os.remove(filename)
    fig.savefig(filename)



def plot_graphs(Gs, ssizes, filename, layout=nx.kamada_kawai_layout):
    nr, nc = ssizes
    totalsize = float(24. / math.sqrt(nc * nr))
    fig = plt.figure(1, figsize=(int(totalsize * nc), int(totalsize * nr)))
    plt.clf()
    splts = fig.subplots(nrows=nr, ncols=nc)
    if nr == 1:
        splts = [splts]
    if nc == 1:
        splts = [splts]
    for i, j in [[y, x] for y in range(nr) for x in range(nc)]:
        G, title = Gs[i * nc + j]
        pos = layout(G, dim=2)
        ax = splts[i][j]
        plt.sca(ax)
        if len(G) < 15:
            nx.draw_networkx_labels(G, pos,
                                    labels={i : str(i) for i in list(G.nodes)},
                                    font_size=25,
                                    font_family='arial-black',
                                    font_weight='bold',
                                    font_color='w',
                                    alpha=1.,
                                    ax=ax)
        color = 'r'
        if nc == 2 and nr == 1 and j == 1:
            color = 'b'
        nx.draw_networkx_nodes(G, pos,
                               node_color=color,
                               node_size=1800,
                               ax=ax)
        nx.draw_networkx_edges(G, pos,
                               width=[0.3 for (u, v, d) in G.edges(data=True)],
                               ax=ax,)
        ax.set_title(title, fontsize=40)
        ax.set_axis_off()
    save_figure(plt, filename)
    plt.clf()
    plt.cla()


def plot_graph(G, filename, layout=nx.kamada_kawai_layout):
    plot_graphs([(G, str(G))], [1, 1], filename, layout)



if __name__ == "__main__":
    plt.switch_backend('agg')
    # plot_graphs([
    #     (nx.tutte_graph(), 'Tutte Graph'),
    #     (nx.barbell_graph(randint(5, 10), randint(5, 10)), 'Barbell Graph'),
    #     (nx.turan_graph(20, 5), 'Turan Graph'),
    #     (nx.lollipop_graph(20, 10), 'Lollipop Graph'),

    #     (nx.circular_ladder_graph(20), 'Circular Ladder Graph'),
    #     (nx.caveman_graph(5, 10), 'Caveman Graph'),
    #     (nx.desargues_graph(), 'Desargues Graph'),
    #     (nx.barabasi_albert_graph(20, 3), 'Barabasi Albert Graph'),

    #     (nx.newman_watts_strogatz_graph(40, 5, .1), 'Newman-Watts-Strogatz Graph'),
    #     (nx.erdos_renyi_graph(40, .1), 'Erdos Renyi Graph'),
    #     (nx.karate_club_graph(), 'Karate Club Graph'),
    #     (nx.hoffman_singleton_graph(), 'Hoffman-Singleton Graph')
    # ], [3, 4], 'families.png')
    # plot_graphs([
    #     (nx.dorogovtsev_goltsev_mendes_graph(i), 'DGM('+str(i)+') Graph')
    #         for i in range(2, 7+1)
    # ], [2, 3], 'dorogovtsev_goltsev_mendes.png')
    # plot_graphs([
    #     (nx.mycielski_graph(i), 'Mycielski('+str(i)+') Graph')
    #         for i in range(1, 10+1)
    # ], [3, 3], 'mycielski.png', nx.spring_layout)
    # plot_graphs([
    #     (nx.margulis_gabber_galil_graph(i), 'MGG('+str(i)+') Graph')
    #         for i in range(1, 13+1)
    # ], [3, 4], 'margulis_gabber_galil.png', nx.spring_layout)
    # n = randint(100, 100)
    # g = nx.random_graphs.binomial_graph(n, .2)
    # plot_graph(g, 'random_graph.png', nx.spring_layout)
    pass


def is_homomorphism(g, h, phi):
    for e in list(g.edges):
        if not (phi[e[0]], phi[e[1]]) in list(h.edges):
            return None
    return phi



def is_homomorphic_recurse(g, h, phi, i):
    if i == len(list(g.nodes)):
        print("phi", phi)
        return is_homomorphism(g, h, phi)
    for k in list(h.nodes):
        phi[i] = k
        r = is_homomorphic_recurse(g, h, phi, i + 1)
        if r is not None:
            return r
    return None


def is_homomorphic(g, h):
    return is_homomorphic_recurse(g, h, [0 for nd in list(g.nodes)], -1)


def make_isomorphic(g):
    pmtnodes = random_permutation(list(g.nodes))
    edges = [(pmtnodes[a], pmtnodes[b]) for (a, b) in list(g.edges)]
    return nx.Graph(edges)


if __name__ == "__main__":
    # g = nx.random_graphs.binomial_graph(8, .4)
    g = nx.desargues_graph()
    phi = is_homomorphic(g, g)
    plot_graphs([
        (g, '$ Dom(\phi) $'),
        (g.subgraph(set(list(phi))), '$ Im(\phi) $')
    ], [1, 2], 'current_random.png')
