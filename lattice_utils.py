import os
import sys
import subprocess
import math

from networkx.drawing.nx_agraph import graphviz_layout
import cairo

from graph_utils import *
from homomorphism_solver import *
from lattice_utils import *


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
            return '#00AAAA'
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


def plot_lattice(g, filename, **kwargs):
    plt.figure(figsize=(16, 16))
    plt.suptitle('lattice',
                 size=35,
                 family='monospace',
                 weight='bold')

    ax = plt.subplot(111)
    nodelist = list(g.nodes())
    nodelist_neighborhood = nodelist
    new_g = g

    if len(nodelist) > 100:
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

    no_nodes = len(nodelist_neighborhood)
    fontsize = 9 - int(math.log(no_nodes, 5))
    nodesize_min = 150 - 20 * int(math.log(no_nodes, 5))
    nodesize_max = 700 - 100 * int(math.log(no_nodes, 5))
    nodesize_step = 200 - 10 * int(math.log(no_nodes, 5))
    nx.draw_networkx(new_g,
                     arrows=True,
                     # pos=graphviz_layout(new_g),
                     pos=nx.kamada_kawai_layout(new_g, dim=2),
                     # pos=nx.spring_layout(g, dim=2),
                     nodelist=nodelist_neighborhood,
                     labels={nd : label_rename(nd) for nd in nodelist},
                     font_size=fontsize,
                     # font_family='arial',
                     font_weight='bold',
                     font_color='k',
                     alpha=1.,
                     node_color=[node_color_func(nd) for nd in nodelist_neighborhood],
                     # node_size=[500 for nd in nodelist_neighborhood],
                     node_size=[(max(nodesize_min, nodesize_max - nodesize_step * (new_g.degree(nd) - 2)) if nd in nodelist else 30)
                                for nd in nodelist_neighborhood],
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
    print('generated plot image', filename)


def graph_color(fname):
    red = (1, 0, 0)
    green = (0, 1, 0)
    blue = (0, 0, 1)
    yellow = (1, 1, 0)
    purple = (1, 0, 1)
    cyan = (0, .7, .7)
    black = (0, 0, 0)
    gray = (.5, .5, .5)
    white = (1, 1, 1)
    g = None
    with open(fname, 'r') as f:
        g = deserialize_graph(f.read())
    if is_path(g):
        return gray
    elif is_cycle(g):
        return yellow
    elif is_complete(g):
        return green
    elif len(g.nodes()) <= 5:
        return cyan
    return white


def plot_adjacency_matrix(g, filename):
    red = (1, 0, 0)
    green = (0, 1, 0)
    blue = (0, 0, 1)
    yellow = (1, 1, 0)
    purple = (1, 0, 1)
    cyan = (0, .7, .7)
    black = (0, 0, 0)
    gray = (.5, .5, .5)
    white = (1, 1, 1)

    colors = [
        # (1, 0, 0),
        # (0, 1, 0),
        # (0, 0, 1),
        # (0, 0, 0),
        # (1, 0, 1),
        # (0, 1, 1)
        black
    ]
    get_color = lambda n: colors[n % len(colors)]
    size = len(g.nodes())
    svg_fname = filename.replace('.png', '.svg')
    with cairo.SVGSurface(svg_fname, size, size) as surface:
        ctx = cairo.Context(surface)
        n = len(g)
        rectsize = float(size) / n
        g_nodes = list(g.nodes())
        color_priority = [gray, yellow, green, cyan, white]
        for i in range(n):
            row_color = graph_color(g_nodes[i])
            for j in range(n):
                col_color = graph_color(g_nodes[j])
                cell_color = row_color
                if col_color in color_priority and color_priority.index(col_color) < color_priority.index(cell_color):
                    cell_color = col_color

                if g.has_edge(g_nodes[i], g_nodes[j]) or nx.has_path(g, g_nodes[i], g_nodes[j]):
                    cr, cg, cb = cell_color
                    ctx.rectangle(i * rectsize, j * rectsize, rectsize, rectsize)
                    ctx.set_source_rgba(cr, cg, cb, 1.)
                    ctx.fill()
            ctx.stroke()
    print('finished creating a diagram')
    subprocess.check_call(['convert', svg_fname, filename])
    os.remove(svg_fname)
    print('generated adjacency matrix', filename)
