#!/usr/bin/env python3


import sys

from graph_utils import *
from homomorphism_solver import is_homomorphic
from lattice_utils import *
from lattice_visualization_utils import graph_label_rename


def make_temporary_graph_file(g):
    filename = 'tempgraphfile_%s_%s.json' % (len(g.nodes()), randint(0, int(1e12)))
    with open(filename, 'w') as f:
        json.dump(serialize_graph(g), f)
    return filename


if __name__ == '__main__':
    plt.switch_backend('agg')
    gfile = sys.argv[1]
    g = load_graph(gfile)
    lattice = Lattice.load('lattice.json')
    powers = [g]
    for p in range(len(powers), 4 + 1):
        powers += [nx.tensor_product(powers[-1], g)]
        G = nx.relabel_nodes(powers[-1], dict(zip(powers[-1].nodes(), range(len(powers[-1])))))
        H = nx.relabel_nodes(powers[-2], dict(zip(powers[-2].nodes(), range(len(powers[-2])))))
        gfile = make_temporary_graph_file(G)
        hfile = make_temporary_graph_file(H)
        if not lattice.is_homomorphic(gfile, hfile):
            print('break')
            break
        os.remove(gfile)
        os.remove(hfile)
        print('power', p)
    plot_graphs([
                    (powers[i], '${' + graph_label_rename(gfile)[1:-1] + '}^{' + str(i) + '}$')
                        for i in range(len(powers))
                ],
                ssizes=[2, 2],
                colors=['r'],
                filename='graph_powers.png',
                node_size=400,
                label_font_size=9,
                title_font_size=25)
