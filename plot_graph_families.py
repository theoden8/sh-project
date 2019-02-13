#!/usr/bin/env python3


import networkx.generators.classic
import networkx.generators.community
import networkx.generators.random_graphs


from graph_utils import *


if __name__ == "__main__":
    plt.switch_backend('agg')
    opts = {
        'node_size': 400,
        'label_font_size': 8,
        'title_font_size': 35
    }
    plot_graphs([
        (nx.tutte_graph(), 'Tutte Graph'),
        (nx.barbell_graph(randint(5, 10), randint(5, 10)), 'Barbell Graph'),
        (nx.turan_graph(20, 5), 'Turan Graph'),
        (nx.lollipop_graph(20, 10), 'Lollipop Graph'),

        (nx.circular_ladder_graph(20), 'Circular Ladder Graph'),
        (nx.caveman_graph(5, 10), 'Caveman Graph'),
        (nx.desargues_graph(), 'Desargues Graph'),
        (nx.barabasi_albert_graph(20, 3), 'Barabasi Albert Graph'),

        (nx.newman_watts_strogatz_graph(40, 5, .1), 'Newman-Watts-Strogatz Graph'),
        (nx.erdos_renyi_graph(40, .1), 'Erdos Renyi Graph'),
        (nx.karate_club_graph(), 'Karate Club Graph'),
        (nx.hoffman_singleton_graph(), 'Hoffman-Singleton Graph')
    ], ssizes=[3, 4], filename='families.png', **opts)
    plot_graphs([
        (nx.dorogovtsev_goltsev_mendes_graph(i), 'DGM('+str(i)+') Graph')
            for i in range(2, 7+1)
    ], ssizes=[2, 3], filename='family_dgm.png', **opts)
    plot_graphs([
        (nx.mycielski_graph(i), 'Mycielski('+str(i)+') Graph')
            for i in range(1, 10+1)
    ], ssizes=[3, 3], filename='family_mycielski.png', layout=nx.spring_layout, **opts)
    plot_graphs([
        (nx.margulis_gabber_galil_graph(i), 'MGG('+str(i)+') Graph')
            for i in range(1, 13+1)
    ], ssizes=[3, 4], filename='family_mgg.png', layout=nx.spring_layout, **opts)
    plot_graph(nx.random_graphs.binomial_graph(randint(100, 100), .2), filename='random_graph.png', layout=nx.spring_layout, **opts)
