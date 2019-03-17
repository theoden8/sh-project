import os
import sys
import subprocess
import math

from networkx.drawing.nx_agraph import graphviz_layout
import cairo

from graph_utils import *
from homomorphism_solver import *
from lattice_utils import *


def get_graph_size(gfile):
    fname = os.path.basename(gfile)
    return int(fname.split('_')[1])


class LatticePathFinder:
    def __init__(self, lattice, nonedges):
        self.lattice = lattice
        self.significant_nodes = [nd for nd in self.lattice.g.nodes() if self.check_node_significance(nd)]
        self.core_graph = None
        self.core_graph_c = None
        self.update_core_graph(nonedges)

    def update_core_graph(self, nonedges):
        subgraph = self.lattice.g.subgraph(self.significant_nodes)

        self.core_graph = nx.DiGraph(subgraph.edges())
        self.core_graph.add_nodes_from(self.significant_nodes)

        self.core_graph_c = nx.DiGraph()
        self.core_graph_c.add_nodes_from(self.significant_nodes)
        for a in nonedges:
            a = self.get_equivalent_node(a)
            for b in nonedges[a]:
                b = self.get_equivalent_node(b)
                if not self.is_known_non_homomorphism(a, b):
                    self.core_graph_c.add_edge(a, b)

    def update_node_significance(self, nd):
        should_contain = self.check_node_significance(nd)
        if should_contain and not self.is_significant_node(nd):
            self.significant_nodes += [nd]

            self.core_graph.add_node(nd)
            for candidate in self.significant_nodes:
                if self.lattice.g.has_edge(candidate, nd):
                    self.core_graph.add_edge(candidate, nd)
                if self.lattice.g.has_edge(nd, candidate):
                    self.core_graph.add_edge(nd, candidate)
            self.core_graph_c.add_node(nd)
        elif not should_contain and self.is_significant_node(nd):
            index = self.significant_nodes.index(nd)
            del self.significant_nodes[index]
            self.core_graph.remove_node(nd)
            self.core_graph_c.remove_node(nd)

    def get_equivalent_node(self, nd):
        g = self.lattice.g
        if self.is_significant_node(nd):
            return nd
        for nb in g.neighbors(nd):
            if self.is_significant_node(nb):
                return nb
        return nd

    def is_significant_node(self, nd):
        return nd in self.significant_nodes

    def check_node_significance(self, nd):
        g = self.lattice.g
        if g.in_degree(nd) == 0 or g.out_degree(nd) == 0:
            return True
        for nb in g.neighbors(nd):
            if nb not in g.predecessors(nd):
                return True
        for nb in g.predecessors(nd):
            if nb not in g.neighbors(nd):
                return True
        if get_graph_size(nd) == 2:
            return True
        return False

    def is_known_homomorphism(self, a, b):
        a = self.get_equivalent_node(a)
        b = self.get_equivalent_node(b)
        return a == b or self.core_graph.has_edge(a, b) or nx.has_path(self.core_graph, a, b)

    def is_known_non_homomorphism(self, a, b):
        a = self.get_equivalent_node(a)
        b = self.get_equivalent_node(b)
        return a != b and self.core_graph_c.has_edge(a, b) and nx.has_path(self.core_graph_c, a, b)

    def is_known_relation(self, a, b):
        return self.is_known_homomorphism(a, b) or self.is_known_non_homomorphism(a, b)

    def memoize_relation(self, a, b, relation):
        if self.is_known_relation(a, b):
            return
        a = self.get_equivalent_node(a)
        b = self.get_equivalent_node(b)
        #print('memoized', a, b, relation)
        if relation:
            self.core_graph.add_edge(a, b)
        else:
            self.core_graph_c.add_edge(a, b)

    def normalize_memoization(self, a):
        if self.is_significant_node(a):
            return
        #print('normalizing', a)
        equiv = self.get_equivalent_node(a)
        if a == equiv:
            return
        if a in self.core_graph.nodes():
            self.core_graph.remove_node(a)
            self.core_graph_c.remove_node(a)

    def has_path(self, a, b):
        # replace nodes with their equivalents
        if self.is_known_homomorphism(a, b):
            return True
        elif self.is_known_non_homomorphism(a, b):
            return False
        a = self.get_equivalent_node(a)
        b = self.get_equivalent_node(b)
        return nx.has_path(self.core_graph, a, b)

    def can_remove_edge(self, a, b):
        #print('trying to remove edge', a, b)
        if self.lattice.g.out_degree(a) == 1 or self.lattice.g.in_degree(b) == 1:
            return False
        for path in nx.all_simple_paths(self.core_graph, a, b):
            if len(path) > 2:
                #print('succeeded removing edge')
                return True
        return False


class LatticeGraphCache:
    def __init__(self, lattice):
        self.lattice = lattice
        self.cache = {}

    def update(self):
        for fname in list(self.cache.keys()):
            if fname not in self.lattice.path_finder.significant_nodes:
                del self.cache[fname]
        for fname in self.lattice.path_finder.significant_nodes:
            if fname not in self.cache:
                self.cache[fname] = self.load(fname)

    def load(self, fname):
        if fname in self.cache:
            return self.cache[fname]
        return load_graph(fname)


class Lattice:
    def __init__(self, g, nonedges={}, cores=[]):
        self.g = g
        self.cores = cores
        self.path_finder = LatticePathFinder(self, nonedges)
        self.cache = LatticeGraphCache(self)

    @staticmethod
    def load(filename):
        with open(filename, 'r') as f:
            return deserialize_lattice(f.read())

    def add_object(self, filename):
        nodename = filename
        #print()
        print('adding object', nodename)
        nodes = list(self.g.nodes())
        if nodename in nodes:
            print('already exists', nodename)
            return
        self.g.add_node(nodename)
        self.path_finder.update_node_significance(nodename)
        self.cache.update()
        for other_graph in self.path_finder.significant_nodes:
            if nodename == other_graph:
                continue
            #print('\t<?>', other_graph)
            self.establish_homomorphism(nodename, other_graph)
            self.establish_homomorphism(other_graph, nodename)
            # we found an equivalence to an existing node
            if self.g.has_edge(nodename, other_graph) and self.g.has_edge(other_graph, nodename):
                for nb in list(self.g.neighbors(nodename)):
                    if nb == other_graph:
                        continue
                    self.g.remove_edge(nodename, nb)
                for nb in list(self.g.predecessors(nodename)):
                    if nb == other_graph:
                        continue
                    self.g.remove_edge(nb, nodename)
                self.path_finder.update_node_significance(nodename)
                self.path_finder.normalize_memoization(nodename)
                break

    def is_homomorphic(self, gfile, hfile):
        if gfile == hfile:
            return True
        g_known, h_known = gfile in self.g.nodes(), hfile in self.g.nodes()
        if g_known and h_known:
            if self.path_finder.is_known_relation(gfile, hfile):
                return self.path_finder.has_path(gfile, hfile)
        elif g_known and not h_known:
            nonedges = []
            equiv = self.path_finder.get_equivalent_node(equiv)
            if equiv in self.core_graph_c.nodes():
                nonedges = list(self.path_finder.core_graph_c.neighbors(equiv))
            nonedges = [nd for nd in nonedges if get_graph_size(nd) <= get_graph_size(gfile)]
            for nh in nonedges:
                print('test %s -> %s' % (nh, hfile))
                if self.find_homomorphism(nh, hfile) is not None:
                    return False
        elif not g_known and h_known:
            pass
        print('test %s -> %s' % (gfile, hfile))
        return self.find_homomorphism(gfile, hfile) is not None

    def is_homomorphic_eq(self, gfile, hfile):
        return self.is_homomorphic(gfile, hfile) and self.is_homomorphic(hfile, gfile)

#     def is_core(self, gfile):
#         if gfile in self.cores:
#             return True
#         G = load_graph(gfile)
        # if is_complete(G) or is_cycle(G):
        #     return True
#         for hfile in nx.dfs_tree(self.g, gfile).nodes():
#             # can't be larger
#             if gfile == hfile or get_graph_size(hfile) > get_graph_size(gfile):
#                 continue
#             # must be homomorphically equivalent
#             if not self.is_homomorphic(hfile, gfile):
#                 continue
#             # we don't care if it's not an edge-induced subgraph
#             H = load_graph(hfile)
#             if not nx.isomorphism.GraphMatcher(nx.line_graph(G), nx.line_graph(H)).subgraph_is_isomorphic():
#                 continue
#             # must not be a core
#             return self.is_core(hfile)
#         return True

    def find_homomorphism(self, gfile, hfile):
        G, H = self.cache.load(gfile), self.cache.load(hfile)
        return is_homomorphic(G, H)

    def add_edge(self, gfile, hfile):
        #print('add edge', gfile, hfile)
        self.g.add_edge(gfile, hfile)
        if self.g.has_edge(hfile, gfile):
            self.path_finder.update_node_significance(gfile)
            self.path_finder.update_node_significance(hfile)

    def remove_edge(self, gfile, hfile):
        if self.path_finder.can_remove_edge(gfile, hfile):
            self.g.remove_edge(gfile, hfile)
            self.path_finder.update_node_significance(gfile)
            self.path_finder.update_node_significance(hfile)
            #print('\t%s /-> %s' % (gfile, out))

    def establish_homomorphism(self, gfile, hfile):
        if self.path_finder.is_known_relation(gfile, hfile):
            return self.path_finder.has_path(gfile, hfile)
        
        if not self.path_finder.is_significant_node(gfile) or not self.path_finder.is_significant_node(hfile):
            return None
        assert self.path_finder.is_significant_node(hfile)
        #print('establish homomorphism', gfile, hfile)

        phi = self.find_homomorphism(gfile, hfile)
        if phi is None:
            self.path_finder.memoize_relation(gfile, hfile, False)
            return False
        reach_nodes = [nd for nd in nx.dfs_tree(self.path_finder.core_graph, hfile).nodes()
                       if nd != hfile and self.path_finder.has_path(hfile, nd)]
        self.add_edge(gfile, hfile)
        #print('%s -> %s' % (gfile, hfile))
        for out in reach_nodes:
            if self.g.has_edge(gfile, out):
                self.remove_edge(gfile, out)
        self.path_finder.memoize_relation(gfile, hfile, True)
        return True


def serialize_lattice(lattice):
    j = serialize_graph(lattice.g)
    j['nonedges'] = {
        u : [v for v in lattice.path_finder.core_graph_c.neighbors(u)]
            for u in lattice.path_finder.core_graph_c.nodes()
                
    }
    j['cores'] = lattice.cores
    return j


def deserialize_lattice(s):
    j = json.loads(s)
    g = deserialize_digraph(json.dumps({'nodes':j['nodes'],'edges':j['edges']}))
    nonedges = j['nonedges']
    cores = j['cores'] if 'cores' in j else []
    return Lattice(g, nonedges, cores)


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
        g = load_graph(fname)
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
        g = load_graph(fname)
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
        elif n == 7:
            return '#FF99FF'
        elif n >= 8:
            return '#AA00AA'
    return '#FFCCCC'


def filter_significant_nodes(g, label):
    if g.in_degree(label) != 1 or g.out_degree(label) != 1:
        return True
    nb = list(g.neighbors(label))[0]
    if g.has_edge(nb, label):
        return False
    return True


def filter_nodes_neighborhood(g, nodelist, label):
    N = get_graph_size(label)
    if N < 8 or N >= 10:
        return True
    return label in nodelist


def plot_lattice(lattice, filename, **kwargs):
    plt.figure(figsize=(16, 16))
    plt.suptitle('lattice',
                 size=35,
                 family='monospace',
                 weight='bold')

    g = lattice.g
    ax = plt.subplot(111)
    nodelist = list(g.nodes())
    nodelist_neighborhood = nodelist
    new_g = g

    if len(nodelist) > 100:
        #nodelist = [nd for nd in g.nodes() if filter_significant_nodes(g, nd)]
        nodelist = lattice.path_finder.significant_nodes
        nodelist_neighborhood = [nd for nd in g.nodes() if filter_nodes_neighborhood(g, nodelist, nd)]
        if len(nodelist_neighborhood) > 1000:
            nodelist_neighborhood = nodelist
        new_g = g.subgraph(nodelist_neighborhood)
        # nodelist = [nd for nd in g.nodes() if filter_important_nodes(g, nd)]
        # print('filtered significant nodes')
        # nodelist_neighborhood = [ndm for ndm in g.nodes()
        #                          if ndm in nodelist or (filter_important_nodes_neighborhood(g, nodelist, ndm)
        #                             and 'small_graphs' in ndm)]

#         new_g = g
#         for e in g.edges():
#             u, v = e
#             if v in nodelist_neighborhood:
#                 continue
#             if new_g.has_edge(u, v):
#                 new_g = nx.contracted_edge(new_g, e)
        # print('reduced insignificant loops')

    no_nodes = len(nodelist_neighborhood)
    # fontsize = 9 - int(math.log(no_nodes, 5))
    # nodesize_min = 150 - 20 * int(math.log(no_nodes, 5))
    # nodesize_max = 700 - 100 * int(math.log(no_nodes, 5))
    # nodesize_step = 200 - 10 * int(math.log(no_nodes, 5))
    nx.draw_networkx(new_g,
                     arrows=True,
                     # pos=graphviz_layout(new_g),
                     pos=nx.kamada_kawai_layout(new_g, dim=2),
                     # pos=nx.spring_layout(g, dim=2),
                     nodelist=nodelist_neighborhood,
                     labels={nd : label_rename(nd) for nd in nodelist},
                     font_size=9,
                     # font_family='arial',
                     font_weight='bold',
                     font_color='k',
                     alpha=1.,
                     node_color=[node_color_func(nd) for nd in nodelist_neighborhood],
                     # node_size=[500 for nd in nodelist_neighborhood],
                     node_size = [(500 if nd in nodelist else 30) for nd in nodelist_neighborhood],
                     # node_size=[(max(nodesize_min, nodesize_max - nodesize_step * (new_g.degree(nd) - 2)) if nd in nodelist else 30)
                     #            for nd in nodelist_neighborhood],
                     edge_color=[('m' if g.has_edge(e[1], e[0]) else 'k') if g.has_edge(e[0], e[1]) else 'b' for e in new_g.edges()],
                     width=[(0.2 if g.has_edge(e[1], e[0]) else 0.4) if g.has_edge(e[0], e[1]) else 0.4 for e in new_g.edges()],
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
    g = load_graph(fname)
    if is_path(g):
        return gray
    elif is_cycle(g):
        return yellow
    elif is_complete(g):
        return green
    elif len(g.nodes()) <= 5:
        return cyan
    return black


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

        ctx.rectangle(0, 0, float(size), float(size))
        ctx.set_source_rgba(1., 1., 1., 1.)
        ctx.fill()

        n = len(g)
        rectsize = float(size) / n
        g_nodes = list(g.nodes())
        color_priority = [gray, yellow, green, cyan, black]
        def sort_func(gfile):
            with open(gfile, 'r') as f:
                g = deserialize_digraph(f.read())
            n = get_graph_size(gfile)
            e = len(g.edges())
            return n * 10000 + e
        g_nodes.sort(key=sort_func)
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
    subprocess.check_call(['rsvg-convert', svg_fname, '-o', filename])
    os.remove(svg_fname)
    print('generated adjacency matrix', filename)
