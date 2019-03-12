#!/usr/bin/env python3


import os
import sys

from graph_utils import *
from homomorphism_solver import *


class Lattice:
    def __init__(self, g):
        self.g = g

    def add_object(self, filename):
        nodename = filename
        nodes = list(self.g.nodes())
        if nodename in nodes:
            print('already exists', nodename)
            return
        self.g.add_node(nodename)
        for other_graph in nodes:
            self.establish_order(nodename, other_graph)
            self.establish_order(other_graph, nodename)

    def establish_order(self, gfile, hfile):
        G, H = None, None
        if nx.has_path(self.g, gfile, hfile):
            return
        with open(gfile, 'r') as f:
            G = deserialize_graph(f.read())
        reach = nx.dfs_tree(self.g, hfile)
        reach_nodes = list(reach.nodes())
        with open(hfile, 'r') as f:
            H = deserialize_graph(f.read())
        phi = is_homomorphic(G, H)
        # print(gfile, hfile, phi)
        if phi is not None:
            print('%s -> %s' % (gfile, hfile))
            for out in reach_nodes:
                if self.g.has_edge(gfile, out):
                    self.g.remove_edge(gfile, out)
                    print('\t%s /-> %s' % (gfile, out))
            self.g.add_edge(gfile, hfile)

def is_complete(g):
    for u in range(len(g.nodes())):
        for v in range(len(g.nodes())):
            if u != v and not g.has_edge(u, v):
                return False
    return True

def is_path(g):
    # we know it's connected
    leaves = 0
    for nd in g.nodes():
        if g.degree(nd) == 1:
            leaves += 1
        elif g.degree(nd) != 2:
            return False
        if leaves > 2:
            return False
    return nx.is_tree(g) and leaves == 2


def label_rename(label):
    fname = label
    is_small = 'small_graphs' in os.path.dirname(label)
    label = os.path.basename(label).replace('graph_', '')
    label = label.replace('.json', '')
    n, id = label.split('_')
    n, id = int(n), int(id)
    if is_small:
        g = None
        with open(fname, 'r') as f:
            g = deserialize_graph(f.read())
        if is_path(g):
            return '$P_%s$' % n
        elif is_complete(g):
            return '$K_%s$' % n
    return '$G^{%s}_{%s}$' % (id % 1000, n)


def node_color_func(label):
    is_small = 'small_graphs' in os.path.dirname(label)
    if is_small:
        return '#CCCCFF'
    return '#FFCCCC'


def plot_lattice(g, filename, **kwargs):
    plt.figure(figsize=(24, 24))
    plt.suptitle('lattice',
                 size=35,
                 family='monospace',
                 weight='bold')

    ax = plt.subplot(111)
    nx.draw_networkx(g,
                     arrows=True,
                     pos=nx.kamada_kawai_layout(g, dim=2),
                     # labels={nd : make_latex_element(nd) for nd in g.nodes()},
                     labels={nd : label_rename(nd) for nd in g.nodes()},
                     font_size=14,
                     # font_family='arial',
                     font_weight='bold',
                     font_color='k',
                     edge_color='k',
                     alpha=1.,
                     node_color=[node_color_func(nd) for nd in g.nodes()],
                     node_size=600,
                     width=[0.3 for (u, v, d) in g.edges(data=True)],
                     arrowstyle='-|>',
                     arrowsize=12,
                     ax=ax)
    # ax.set_title('Lattice', fontsize=40)
    ax.set_axis_off()

    if os.path.exists(filename):
        os.remove(filename)
    plt.savefig(filename)
    plt.clf()
    plt.cla()
    plt.close()


if __name__ == '__main__':
    plt.switch_backend('agg')
    dbfile = './lattice.json'
    g = nx.DiGraph()
    if os.path.exists(dbfile):
        with open(dbfile, 'r') as f:
            g = deserialize_digraph(f.read())
    print(list(g.nodes()))

    lattice = Lattice(g)
    for graph_file in sys.argv[1:]:
        lattice.add_object(graph_file)

    with open(dbfile, 'w') as f:
        json.dump(serialize_graph(g), f)
    if len(g.nodes()) > 0:
        plot_lattice(g, 'lattice.png')
