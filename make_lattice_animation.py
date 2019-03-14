#!/usr/bin/env python3


import sys

from graph_utils import *
from lattice_utils import *


def sort_func(gfile):
    with open(gfile, 'r') as f:
        g = deserialize_graph(f.read())
        return len(g.nodes()) * 10000 + len(g.edges())


def get_all_lattice_nodes(lattice_fname):
    if not os.path.exists(lattice_fname):
        return None
    g = None
    with open(lattice_fname, 'r') as f:
        g = deserialize_digraph(f.read())
    nodes = list(g.nodes())
    nodes.sort(key=sort_func)
    return nodes


if __name__ == '__main__':
    plt.switch_backend('agg')

    if not os.path.exists('frames'):
        os.mkdir('./frames/')

    nodes = get_all_lattice_nodes('./lattice.json')

    lattice = Lattice(nx.DiGraph())

    i = 0
    for nd in nodes:
        frame_name = 'frames/frame_%d.png' % i
        frame_lattice_name = 'frames/frame_lattice_%d.json' % i
        # if the lattice doesn't exist, create it and save
        if not os.path.exists(frame_lattice_name):
            lattice.add_object(nd)
            with open(frame_lattice_name, 'w') as f:
                json.dump(serialize_graph(lattice.g), f)
        # if it does, just play it
        else:
            new_g = None
            with open(frame_lattice_name, 'r') as f:
                new_g = deserialize_digraph(f.read())
            lattice = Lattice(new_g)
        if not os.path.exists(frame_name):
            print('making new frame', frame_name)
            plot_lattice(lattice.g, frame_name)
        i += 1