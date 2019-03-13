#!/usr/bin/env python3


import os
import sys

from networkx.drawing.nx_agraph import graphviz_layout

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
        not_connected = []
        for other_graph in nodes:
            should_check = True
            for not_homomorphic in not_connected:
                if nx.has_path(self.g, other_graph, not_homomorphic):
                    should_check = False
                    break
            if should_check:
                result = self.establish_order(nodename, other_graph)
                if not result:
                    not_connected += [other_graph]
            self.establish_order(other_graph, nodename)

    def establish_order(self, gfile, hfile):
        G, H = None, None
        if nx.has_path(self.g, gfile, hfile):
            return True
        with open(gfile, 'r') as f:
            G = deserialize_graph(f.read())
        reach = nx.dfs_tree(self.g, hfile)
        reach_nodes = list(reach.nodes())
        with open(hfile, 'r') as f:
            H = deserialize_graph(f.read())
        phi = is_homomorphic(G, H)
        if phi is None:
            return False
        print('%s -> %s' % (gfile, hfile))
        for out in reach_nodes:
            if self.g.has_edge(gfile, out) and nx.has_path(self.g, hfile, out):
                self.g.remove_edge(gfile, out)
                print('\t%s /-> %s' % (gfile, out))
        self.g.add_edge(gfile, hfile)
        return True


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


def is_cycle(g):
    for nd in g.nodes():
        if g.degree(nd) != 2:
            return False
    return True


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
        elif is_cycle(g):
            return '$C_%s$' % n
        elif is_complete(g):
            return '$K_%s$' % n
    return '${%s}^{%s}$' % (n, id % 1000)


def node_color_func(label):
    fname = label
    is_small = 'small_graphs' in os.path.dirname(label)
    if is_small:
        n = int(os.path.basename(label).split('_')[1])
        g = None
        with open(fname, 'r') as f:
            g = deserialize_graph(f.read())
        if is_path(g):
            return '#CCCCCC'
        elif is_cycle(g):
            return '#FFFFCC'
        elif is_complete(g):
            return '#66FF66'
        elif n <= 5:
            return 'c'#66FFFF'
        elif n == 6:
            return '#9999FF'
        elif n >= 7:
            return '#FF99FF'
    return '#FFCCCC'


def filter_important_nodes(g, label):
    # fname = label
    is_small = 'small_graphs' in os.path.dirname(label)
    if not is_small and g.out_degree(label) == 1:
        return False
    #     return True
    # n = int(os.path.basename(label).split('_')[1])
    # if n <= 4:
    #     return True
    # with open(fname, 'r') as f:
    #     G = deserialize_graph(f.read())
        # if is_path(G) or is_complete(G):
        #     return True
    if g.in_degree(label) == 1 and g.out_degree(label) == 1:
        return False
    return True


def filter_important_nodes_neighborhood(g, nodelist, ndm):
    max_distance = 2
    for nd in nodelist:
        if not nx.has_path(g, ndm, nd):
            continue
        if nx.shortest_path_length(g, ndm, nd) <= max_distance:
            return True
    for nd in nodelist:
        if not nx.has_path(g, nd, ndm):
            continue
        if nx.shortest_path_length(g, nd, ndm) <= max_distance:
            return True
    return False


def is_implicit_path(g, nodes, path):
    # print('path', [list(g.nodes()).index(nd) for nd in path])
    for nd in path[1:-1]:
        # print('break on ', list(g.nodes()).index(nd))
        if nd in nodes:
            return False
    return True


def plot_lattice(g, filename, **kwargs):
    plt.figure(figsize=(16, 16))
    plt.suptitle('lattice',
                 size=35,
                 family='monospace',
                 weight='bold')

    ax = plt.subplot(111)
    nodelist = [nd for nd in g.nodes() if filter_important_nodes(g, nd)]
    print('filtered significant nodes')
    nodelist_neighborhood = [ndm for ndm in g.nodes()
                             if ndm in nodelist or (filter_important_nodes_neighborhood(g, nodelist, ndm)
                                and 'small_graphs' in ndm)]

    new_g = g
    for e in g.edges():
        u, v = e
        if v in nodelist_neighborhood:
            continue
        if new_g.has_edge(u, v):
            new_g = nx.contracted_edge(new_g, e)
    print('reduced insignificant loops')

    nx.draw_networkx(new_g,
                     arrows=True,
                     pos=graphviz_layout(new_g),
                     # pos=nx.kamada_kawai_layout(new_g, dim=2),
                     # pos=nx.spring_layout(g, dim=2),
                     nodelist=nodelist_neighborhood,
                     labels={nd : label_rename(nd) for nd in nodelist},
                     font_size=8,
                     # font_family='arial',
                     font_weight='bold',
                     font_color='k',
                     alpha=1.,
                     node_color=[node_color_func(nd) for nd in nodelist_neighborhood],
                     # node_size=[500 for nd in nodelist_neighborhood],
                     node_size=[(max(150, 600 - 200 * (new_g.degree(nd) - 2)) if nd in nodelist else 30) for nd in nodelist_neighborhood],
                     edge_color=['k' if g.has_edge(e[0], e[1]) else 'b' for e in new_g.edges()],
                     width=[0.2 if g.has_edge(e[0], e[1]) else 0.4 for e in new_g.edges()],
                     arrowstyle='-|>',
                     arrowsize=10,
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
