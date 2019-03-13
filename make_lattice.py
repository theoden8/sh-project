#!/usr/bin/env python3


import os
import sys
import subprocess

from graph_utils import *
from lattice_utils import *


if __name__ == '__main__':
    plt.switch_backend('agg')
    dbfile = './lattice.json'
    g = nx.DiGraph()
    if os.path.exists(dbfile):
        with open(dbfile, 'r') as f:
            g = deserialize_digraph(f.read())
    # g.remove_nodes_from([nd for nd in g.nodes() if 'small_graphs' not in nd])
    # print(list(g.nodes()))

    lattice = Lattice(g)
    for graph_file in sys.argv[1:]:
        graph_file = graph_file.replace('./', '')
        lattice.add_object(graph_file)

    if len(sys.argv) > 1:
        with open(dbfile, 'w') as f:
            json.dump(serialize_graph(g), f)
    if len(g.nodes()) > 0:
        plot_lattice(g, 'lattice.png')
        plot_adjacency_matrix(g, 'lattice_adj.png')
